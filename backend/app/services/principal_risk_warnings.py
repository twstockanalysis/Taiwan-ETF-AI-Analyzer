"""Deterministic principal-risk warnings for a base ETF."""

from datetime import date, timedelta
from decimal import Decimal

from backend.app.models.target_analysis import (
    TargetAnalysisWarning,
    TargetAnalysisWarningCode,
)

PERSISTENT_DECLINE_MONTHS = 3
PERSISTENT_DECLINE_THRESHOLD_PCT = Decimal("-10")
RECOVERY_WINDOW_DAYS = 60
PEER_MINIMUM_COUNT = 5
PEER_UNDERPERFORMANCE_GAP_PCT = Decimal("10")


def _date(value: object) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))


def _decimal(value: object) -> Decimal:
    return Decimal(str(value))


def _persistent_decline_warning(
    closes: list[dict],
) -> TargetAnalysisWarning | None:
    if not closes:
        return None
    latest_source = str(
        max(closes, key=lambda item: _date(item["trade_date"]))["source_id"]
    )
    month_ends: dict[tuple[int, int], dict] = {}
    for row in sorted(
        (
            item
            for item in closes
            if str(item.get("source_id")) == latest_source
        ),
        key=lambda item: _date(item["trade_date"]),
    ):
        trade_date = _date(row["trade_date"])
        month_ends[(trade_date.year, trade_date.month)] = row
    checkpoints = list(month_ends.values())[-(PERSISTENT_DECLINE_MONTHS + 1) :]
    if len(checkpoints) < PERSISTENT_DECLINE_MONTHS + 1:
        return None
    month_indexes = [
        _date(row["trade_date"]).year * 12 + _date(row["trade_date"]).month
        for row in checkpoints
    ]
    if not all(current - previous == 1 for previous, current in zip(
        month_indexes, month_indexes[1:]
    )):
        return None
    prices = [_decimal(row["close_price"]) for row in checkpoints]
    if not all(current < previous for previous, current in zip(prices, prices[1:])):
        return None
    decline_pct = (prices[-1] / prices[0] - Decimal("1")) * Decimal("100")
    if decline_pct > PERSISTENT_DECLINE_THRESHOLD_PCT:
        return None
    latest = checkpoints[-1]
    return TargetAnalysisWarning(
        code=TargetAnalysisWarningCode.PERSISTENT_PRICE_DECLINE,
        message="最近三個月末收盤價連續下跌，且累計跌幅至少 10%。",
        affected_fields=["ending_holding_value", "after_tax_total_return_pct"],
        as_of_date=_date(latest["trade_date"]),
        source_id=str(latest["source_id"]),
        evidence={
            "start_date": _date(checkpoints[0]["trade_date"]),
            "start_close": prices[0],
            "end_close": prices[-1],
            "decline_pct": decline_pct.quantize(Decimal("0.000001")),
            "threshold_pct": PERSISTENT_DECLINE_THRESHOLD_PCT,
            "consecutive_months": PERSISTENT_DECLINE_MONTHS,
        },
    )


def _weak_recovery_warning(
    closes: list[dict], dividends: list[dict], analysis_date: date
) -> TargetAnalysisWarning | None:
    if not closes:
        return None
    latest_source = str(
        max(closes, key=lambda item: _date(item["trade_date"]))["source_id"]
    )
    ordered = sorted(
        (
            item
            for item in closes
            if str(item.get("source_id")) == latest_source
        ),
        key=lambda item: _date(item["trade_date"]),
    )
    for dividend in sorted(
        (item for item in dividends if item.get("ex_dividend_date")),
        key=lambda item: _date(item["ex_dividend_date"]),
        reverse=True,
    ):
        ex_date = _date(dividend["ex_dividend_date"])
        deadline = ex_date + timedelta(days=RECOVERY_WINDOW_DAYS)
        if analysis_date < deadline:
            continue
        before = [item for item in ordered if _date(item["trade_date"]) < ex_date]
        after = [
            item
            for item in ordered
            if ex_date <= _date(item["trade_date"]) <= deadline
        ]
        if not before or not after:
            continue
        reference = before[-1]
        reference_close = _decimal(reference["close_price"])
        maximum_close = max(_decimal(item["close_price"]) for item in after)
        if maximum_close >= reference_close:
            return None
        latest = after[-1]
        return TargetAnalysisWarning(
            code=TargetAnalysisWarningCode.WEAK_PRICE_RECOVERY,
            message="最近一個具完整觀察窗的除息事件，在 60 天內未回到除息前收盤價。",
            affected_fields=["ending_holding_value", "after_tax_total_return_pct"],
            as_of_date=_date(latest["trade_date"]),
            source_id=str(latest["source_id"]),
            evidence={
                "ex_dividend_date": ex_date,
                "recovery_deadline": deadline,
                "reference_close": reference_close,
                "maximum_close": maximum_close,
                "window_days": RECOVERY_WINDOW_DAYS,
                "dividend_source_id": str(dividend.get("source_id") or ""),
            },
        )
    return None


def _peer_warning(
    etf_code: str, selected_performance: dict | None, peers: list[dict]
) -> TargetAnalysisWarning | None:
    if not selected_performance or selected_performance.get("period_code") != "1Y":
        return None
    comparison_date = _date(selected_performance["as_of_date"])
    comparison_source = str(selected_performance["source_id"])
    comparable = [
        row
        for row in peers
        if row.get("sort_return_pct") is not None
        and str(row.get("etf_code")) != etf_code
        and _date(row.get("sort_as_of_date")) == comparison_date
        and str(row.get("sort_source_id")) == comparison_source
    ]
    if len(comparable) < PEER_MINIMUM_COUNT:
        return None
    target_return = _decimal(selected_performance["return_pct"])
    values = sorted(_decimal(row["sort_return_pct"]) for row in comparable)
    middle = len(values) // 2
    peer_median = (
        values[middle]
        if len(values) % 2
        else (values[middle - 1] + values[middle]) / Decimal("2")
    )
    gap = peer_median - target_return
    if gap < PEER_UNDERPERFORMANCE_GAP_PCT:
        return None
    return TargetAnalysisWarning(
        code=TargetAnalysisWarningCode.MATERIAL_PEER_UNDERPERFORMANCE,
        message="一年價格報酬明顯落後同類 ETF 中位數至少 10 個百分點。",
        affected_fields=["annual_price_return_pct", "after_tax_total_return_pct"],
        as_of_date=comparison_date,
        source_id=comparison_source,
        evidence={
            "period_code": "1Y",
            "etf_return_pct": target_return,
            "peer_median_return_pct": peer_median,
            "underperformance_gap_pct": gap,
            "threshold_gap_pct": PEER_UNDERPERFORMANCE_GAP_PCT,
            "peer_count": len(comparable),
        },
    )


def build_principal_risk_warnings(
    *,
    etf_code: str,
    analysis_date: date,
    after_tax_total_return_pct: Decimal | None,
    selected_performance: dict | None,
    daily_closes: list[dict],
    dividends: list[dict],
    peer_performance: list[dict],
) -> list[TargetAnalysisWarning]:
    """Build warnings in stable severity order without inferring missing facts."""

    warnings: list[TargetAnalysisWarning] = []
    if (
        after_tax_total_return_pct is not None
        and after_tax_total_return_pct < 0
        and selected_performance is not None
        and selected_performance.get("as_of_date")
        and selected_performance.get("source_id")
    ):
        performance = selected_performance or {}
        warnings.append(
            TargetAnalysisWarning(
                code=TargetAnalysisWarningCode.NEGATIVE_TOTAL_RETURN,
                message="估算稅後總報酬為負，配息不足以抵銷持有價值變化。",
                affected_fields=["after_tax_total_gain_loss", "after_tax_total_return_pct"],
                as_of_date=_date(performance["as_of_date"]),
                source_id=str(performance["source_id"]),
                evidence={"after_tax_total_return_pct": after_tax_total_return_pct},
            )
        )
    for warning in (
        _persistent_decline_warning(daily_closes),
        _weak_recovery_warning(daily_closes, dividends, analysis_date),
        _peer_warning(etf_code, selected_performance, peer_performance),
    ):
        if warning is not None:
            warnings.append(warning)
    return warnings
