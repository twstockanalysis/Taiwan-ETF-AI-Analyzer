"""V3-5 配置後組合的歷史含息績效與十年情境。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from backend.app.models.allocation_results import AllocationStrategyPlan
from backend.app.models.integer_allocation import IntegerAllocationHoldingResult
from backend.app.models.long_term_scenario import (
    AllocationPlanLongTermEvidence,
    HistoricalEvidenceStatus,
    HistoricalPeriod,
    HistoricalPortfolioEvidence,
    LongTermScenarioBand,
    LongTermScenarioRequest,
    LongTermScenarioResponse,
    ScenarioBand,
    ScenarioIndexPoint,
)
from backend.app.models.public_planner import PublicPlannerIssue
from backend.app.repositories.daily_close_repository import list_daily_closes
from backend.app.repositories.dividend_repository import list_etf_dividends
from backend.app.services.allocation_results import build_allocation_results
from backend.app.utils.date_tools import shift_months


_MONEY = Decimal("0.01")
_PCT = Decimal("0.000001")
_DAYS_PER_YEAR = Decimal("365.2425")


@dataclass(frozen=True, slots=True)
class _HoldingHistory:
    holding: IntegerAllocationHoldingResult
    closes: dict[date, Decimal]
    dividends: tuple[dict, ...]


def _money(value: Decimal) -> Decimal:
    return value.quantize(_MONEY, rounding=ROUND_HALF_UP)


def _pct(value: Decimal) -> Decimal:
    return value.quantize(_PCT, rounding=ROUND_HALF_UP)


def _issue(code: str, message: str) -> PublicPlannerIssue:
    return PublicPlannerIssue(code=code, message=message)


def _parsed_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None
    return None


def _load_histories(
    holdings: list[IntegerAllocationHoldingResult],
    database_path: str | Path,
    analysis_date: date,
) -> tuple[list[_HoldingHistory], list[PublicPlannerIssue]]:
    histories = []
    issues = []
    for holding in holdings:
        closes = {
            parsed: Decimal(str(row["close_price"]))
            for row in list_daily_closes(holding.etf_code, database_path)
            if row.get("source_id") == holding.reference_price_source_id
            and (parsed := _parsed_date(row.get("trade_date"))) is not None
            and parsed <= analysis_date
        }
        if not closes:
            issues.append(
                _issue(
                    "PRICE_HISTORY_UNAVAILABLE",
                    f"{holding.etf_code} 缺少同來源的歷史收盤價。",
                )
            )
        histories.append(
            _HoldingHistory(
                holding=holding,
                closes=closes,
                dividends=tuple(
                    list_etf_dividends(
                        holding.etf_code,
                        database_path,
                        limit=10_000,
                    )
                ),
            )
        )
    return histories, issues


def _unavailable(
    period: HistoricalPeriod,
    code: str,
    message: str,
) -> HistoricalPortfolioEvidence:
    return HistoricalPortfolioEvidence(
        period=period,
        status=HistoricalEvidenceStatus.UNAVAILABLE,
        issues=[_issue(code, message)],
    )


def _common_dates(histories: list[_HoldingHistory]) -> list[date]:
    if not histories or any(not history.closes for history in histories):
        return []
    shared = set(histories[0].closes)
    for history in histories[1:]:
        shared.intersection_update(history.closes)
    return sorted(shared)


def _period_evidence(
    period: HistoricalPeriod,
    histories: list[_HoldingHistory],
    deduction_rate_pct: Decimal,
    *,
    target_start: date | None = None,
    target_end: date | None = None,
) -> HistoricalPortfolioEvidence:
    dates = _common_dates(histories)
    if len(dates) < 2:
        return _unavailable(
            period,
            "COMMON_PRICE_HISTORY_UNAVAILABLE",
            "配置內 ETF 沒有足夠的共同收盤價區間。",
        )
    if target_start is None:
        start = dates[0]
    else:
        candidates = [item for item in dates if item >= target_start]
        if not candidates or (candidates[0] - target_start).days > 14:
            return _unavailable(
                period,
                "PERIOD_PRICE_HISTORY_UNAVAILABLE",
                f"共同價格歷史不足以計算 {period.value}。",
            )
        start = candidates[0]
    if target_end is None:
        end = dates[-1]
    else:
        candidates = [item for item in dates if item <= target_end]
        if not candidates or (target_end - candidates[-1]).days > 14:
            return _unavailable(
                period,
                "PERIOD_END_PRICE_UNAVAILABLE",
                f"{period.value} 缺少可對齊的期末價格。",
            )
        end = candidates[-1]
    observation_days = (end - start).days
    if observation_days <= 0:
        return _unavailable(
            period,
            "NON_POSITIVE_HISTORY_WINDOW",
            "共同價格歷史期間不足一天。",
        )

    start_value = Decimal("0")
    end_value = Decimal("0")
    gross_distributions = Decimal("0")
    for history in histories:
        units = Decimal(history.holding.resulting_shares)
        start_value += history.closes[start] * units
        end_value += history.closes[end] * units
        for event in history.dividends:
            payment_date = _parsed_date(event.get("payment_date"))
            event_date = next(
                (
                    parsed
                    for field in (
                        "ex_dividend_date",
                        "record_date",
                        "announcement_date",
                    )
                    if (parsed := _parsed_date(event.get(field))) is not None
                ),
                None,
            )
            if payment_date is None:
                if event_date is not None and start <= event_date <= end:
                    return _unavailable(
                        period,
                        "MISSING_PAYMENT_DATE",
                        f"{history.holding.etf_code} 的區間配息缺少付款日。",
                    )
                continue
            if start <= payment_date <= end:
                if event.get("currency") != "TWD":
                    return _unavailable(
                        period,
                        "MIXED_CURRENCY",
                        "區間配息包含非 TWD 幣別，無法直接合併。",
                    )
                gross_distributions += Decimal(
                    str(event.get("amount_per_unit") or 0)
                ) * units

    if start_value <= 0:
        return _unavailable(
            period,
            "NON_POSITIVE_START_VALUE",
            "歷史含息績效缺少正的期初市值。",
        )
    after_distributions = gross_distributions * (
        Decimal("1") - deduction_rate_pct / Decimal("100")
    )
    ending_total = end_value + after_distributions
    total_return = (ending_total / start_value - Decimal("1")) * Decimal("100")
    factor = ending_total / start_value
    if factor == 0:
        annualized = Decimal("-100")
    else:
        years = Decimal(observation_days) / _DAYS_PER_YEAR
        annualized = ((factor.ln() / years).exp() - Decimal("1")) * Decimal("100")
    return HistoricalPortfolioEvidence(
        period=period,
        status=HistoricalEvidenceStatus.AVAILABLE,
        period_start=start,
        period_end=end,
        observation_days=observation_days,
        start_value=_money(start_value),
        end_value=_money(end_value),
        gross_distributions=_money(gross_distributions),
        after_deduction_distributions=_money(after_distributions),
        total_return_pct=_pct(total_return),
        annualized_total_return_pct=_pct(annualized),
    )


def _percentile(values: list[Decimal], percentile: Decimal) -> Decimal:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = percentile / Decimal("100") * Decimal(len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - Decimal(lower)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _annual_observations(
    histories: list[_HoldingHistory],
    deduction_rate_pct: Decimal,
) -> list[Decimal]:
    dates = _common_dates(histories)
    if len(dates) < 2:
        return []
    common_start = dates[0]
    common_end = dates[-1]
    observations = []
    offset = 0
    while True:
        period_end = shift_months(common_end, -12 * offset)
        period_start = shift_months(common_end, -12 * (offset + 1))
        if period_start < common_start:
            break
        evidence = _period_evidence(
            HistoricalPeriod.AVAILABLE_HISTORY,
            histories,
            deduction_rate_pct,
            target_start=period_start,
            target_end=period_end,
        )
        if (
            evidence.status == HistoricalEvidenceStatus.AVAILABLE
            and evidence.annualized_total_return_pct is not None
        ):
            observations.append(evidence.annualized_total_return_pct)
        offset += 1
    return observations


def _scenario_bands(annual_returns: list[Decimal]) -> list[LongTermScenarioBand]:
    definitions = (
        (ScenarioBand.CONSERVATIVE, "保守情境", Decimal("25")),
        (ScenarioBand.BASE, "基準情境", Decimal("50")),
        (ScenarioBand.OPTIMISTIC, "樂觀情境", Decimal("75")),
    )
    results = []
    for band, label, percentile in definitions:
        rate = max(_percentile(annual_returns, percentile), Decimal("-100"))
        factor = Decimal("1") + rate / Decimal("100")
        points = [
            ScenarioIndexPoint(
                year=year,
                total_value_index=_money(Decimal("100") * factor**year),
            )
            for year in range(11)
        ]
        results.append(
            LongTermScenarioBand(
                band=band,
                label=label,
                annual_total_return_assumption_pct=_pct(rate),
                percentile=percentile,
                index_points=points,
            )
        )
    return results


def _plan_evidence(
    plan: AllocationStrategyPlan,
    database_path: str | Path,
    analysis_date: date,
) -> AllocationPlanLongTermEvidence:
    deduction_rate = plan.result.assumptions.cash_deduction_rate_pct
    histories, load_issues = _load_histories(
        plan.result.resulting_holdings,
        database_path,
        analysis_date,
    )
    dates = _common_dates(histories)
    periods = [
        _period_evidence(
            HistoricalPeriod.AVAILABLE_HISTORY,
            histories,
            deduction_rate,
        )
    ]
    common_end = dates[-1] if dates else analysis_date
    for period, years in (
        (HistoricalPeriod.THREE_YEARS, 3),
        (HistoricalPeriod.FIVE_YEARS, 5),
        (HistoricalPeriod.TEN_YEARS, 10),
    ):
        periods.append(
            _period_evidence(
                period,
                histories,
                deduction_rate,
                target_start=shift_months(common_end, -12 * years),
                target_end=common_end,
            )
        )
    annual_returns = _annual_observations(histories, deduction_rate)
    issues = list(load_issues)
    if histories:
        issues.append(
            _issue(
                "UNIT_CHANGE_ADJUSTMENT_UNAVAILABLE",
                "歷史價格為官方原始收盤價，尚未納入 ETF 分割或反分割調整。",
            )
        )
    scenarios = []
    if len(annual_returns) < 2:
        issues.append(
            _issue(
                "INSUFFICIENT_ANNUAL_OBSERVATIONS",
                "少於兩個完整一年期觀察，暫不建立十年情境。",
            )
        )
    else:
        scenarios = _scenario_bands(annual_returns)
    return AllocationPlanLongTermEvidence(
        strategy=plan.strategy,
        historical_periods=periods,
        annual_observation_count=len(annual_returns),
        scenarios=scenarios,
        issues=issues,
    )


def build_long_term_scenarios(
    request: LongTermScenarioRequest,
    database_path: str | Path,
    *,
    as_of_date: date | None = None,
) -> LongTermScenarioResponse:
    analysis_date = as_of_date or date.today()
    allocation_results = build_allocation_results(
        request,
        database_path,
        as_of_date=analysis_date,
    )
    return LongTermScenarioResponse(
        allocation_results=allocation_results,
        plan_evidence=[
            _plan_evidence(plan, database_path, analysis_date)
            for plan in allocation_results.plans
        ],
    )
