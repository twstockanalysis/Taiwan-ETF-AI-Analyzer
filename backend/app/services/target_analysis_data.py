import calendar
from dataclasses import dataclass
from datetime import date

from backend.app.models.etf_analysis import PerformancePeriod


@dataclass(frozen=True)
class PerformancePeriodSelection:
    selected_period: PerformancePeriod
    used_fallback: bool


_PERIOD_YEARS = {
    PerformancePeriod.ONE_YEAR: 1,
    PerformancePeriod.THREE_YEARS: 3,
    PerformancePeriod.FIVE_YEARS: 5,
}


def _add_calendar_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(
        value.day,
        calendar.monthrange(year, month)[1],
    )
    return date(year, month, day)


def is_performance_data_stale(
    performance_date: date,
    as_of_date: date,
) -> bool:
    return (as_of_date - performance_date).days > 10


def is_dividend_data_stale(
    latest_payment_date: date,
    as_of_date: date,
) -> bool:
    stale_after = _add_calendar_months(
        latest_payment_date,
        18,
    )
    return as_of_date > stale_after


def select_performance_period(
    history_years: int,
    available_periods: tuple[PerformancePeriod, ...],
) -> PerformancePeriodSelection | None:
    available_supported = {
        period
        for period in available_periods
        if period in _PERIOD_YEARS
    }

    exact_period = next(
        (
            period
            for period, years in _PERIOD_YEARS.items()
            if years == history_years
            and period in available_supported
        ),
        None,
    )

    if exact_period is not None:
        return PerformancePeriodSelection(
            selected_period=exact_period,
            used_fallback=False,
        )

    shorter_periods = [
        period
        for period in available_supported
        if _PERIOD_YEARS[period] < history_years
    ]

    if not shorter_periods:
        return None

    selected_period = max(
        shorter_periods,
        key=_PERIOD_YEARS.__getitem__,
    )

    return PerformancePeriodSelection(
        selected_period=selected_period,
        used_fallback=True,
    )


@dataclass(frozen=True)
class TargetAnalysisData:
    monthly_income: dict
    dividends: list[dict]
    selected_performance: dict | None
    warnings: list
    unavailable_fields: list


def _parse_date(value) -> date | None:
    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    return None


def load_target_analysis_data(
    *,
    etf_code: str,
    database_path,
    history_years: int,
    as_of_date: date,
) -> TargetAnalysisData:
    from backend.app.models.target_analysis import (
        TargetAnalysisUnavailableField,
        TargetAnalysisWarning,
        TargetAnalysisWarningCode,
    )
    from backend.app.repositories import (
        dividend_repository,
        monthly_income_repository,
        performance_repository,
    )

    monthly_income = (
        monthly_income_repository
        .build_monthly_income_distribution(
            etf_code=etf_code,
            database_path=database_path,
            lookback_years=history_years,
        )
    )
    dividends = dividend_repository.list_etf_dividends(
        etf_code=etf_code,
        database_path=database_path,
        limit=200,
        offset=0,
    )
    performance_rows = (
        performance_repository
        .list_latest_etf_performance(
            etf_code=etf_code,
            database_path=database_path,
        )
    )

    warnings = []
    warning_codes = set()
    unavailable_fields = []
    unavailable_names = set()

    def add_warning(
        code,
        message: str,
        affected_fields=None,
    ) -> None:
        if code in warning_codes:
            return

        warning_codes.add(code)
        warnings.append(
            TargetAnalysisWarning(
                code=code,
                message=message,
                affected_fields=affected_fields or [],
            )
        )

    def add_unavailable(
        field: str,
        reason: str,
    ) -> None:
        if field in unavailable_names:
            return

        unavailable_names.add(field)
        unavailable_fields.append(
            TargetAnalysisUnavailableField(
                field=field,
                reason=reason,
            )
        )

    missing_yield = any(
        item.get("yield_pct") is None
        for item in dividends
    )
    missing_payment_date = any(
        item.get("payment_date") is None
        for item in dividends
    )

    if missing_yield:
        add_warning(
            TargetAnalysisWarningCode
            .INCOMPLETE_DIVIDEND_DATA,
            "部分配息紀錄缺少殖利率。",
            ["dividend_yield_pct"],
        )
        add_unavailable(
            "dividend_yield_pct",
            "部分配息紀錄缺少殖利率",
        )

    if missing_payment_date:
        add_warning(
            TargetAnalysisWarningCode
            .INCOMPLETE_DIVIDEND_DATA,
            "部分配息紀錄缺少付款日。",
            ["payment_date"],
        )
        add_unavailable(
            "payment_date",
            "部分配息紀錄缺少付款日",
        )

    currencies = {
        item["currency"]
        for item in dividends
        if item.get("currency")
    }
    has_mixed_currencies = bool(
        monthly_income.get(
            "has_mixed_currencies",
            False,
        )
    ) or len(currencies) > 1

    if has_mixed_currencies:
        add_warning(
            TargetAnalysisWarningCode.MIXED_CURRENCY,
            "配息資料包含多種幣別，無法直接合併分析。",
            ["analysis_currency"],
        )
        add_unavailable(
            "analysis_currency",
            "配息資料包含多種幣別",
        )

    payment_dates = [
        parsed
        for item in dividends
        if (
            parsed := _parse_date(
                item.get("payment_date")
            )
        ) is not None
    ]
    required_history_start = _add_calendar_months(
        as_of_date,
        -(history_years * 12),
    )

    if (
        not payment_dates
        or min(payment_dates) > required_history_start
    ):
        add_warning(
            TargetAnalysisWarningCode
            .INSUFFICIENT_DIVIDEND_HISTORY,
            "配息歷史未涵蓋要求的分析期間。",
            ["dividend_history"],
        )

    if (
        payment_dates
        and is_dividend_data_stale(
            max(payment_dates),
            as_of_date,
        )
    ):
        add_warning(
            TargetAnalysisWarningCode
            .STALE_DIVIDEND_DATA,
            "最新配息資料已超過更新期限。",
            ["dividend_history"],
        )

    price_return_rows = [
        item
        for item in performance_rows
        if item.get("metric_code") == "PRICE_RETURN"
    ]
    rows_by_period = {}

    for item in price_return_rows:
        try:
            period = PerformancePeriod(
                item.get("period_code")
            )
        except (TypeError, ValueError):
            continue

        if period in _PERIOD_YEARS:
            rows_by_period[period] = item

    selection = select_performance_period(
        history_years,
        tuple(rows_by_period),
    )
    selected_performance = None

    if selection is None:
        add_warning(
            TargetAnalysisWarningCode
            .INSUFFICIENT_PERFORMANCE_HISTORY,
            "沒有可支援要求期間的價格報酬資料。",
            ["performance_return_pct"],
        )
        add_unavailable(
            "performance_return_pct",
            "沒有可支援要求期間的價格報酬資料",
        )
    else:
        selected_performance = rows_by_period[
            selection.selected_period
        ]

        if selection.used_fallback:
            add_warning(
                TargetAnalysisWarningCode
                .PERFORMANCE_PERIOD_FALLBACK,
                "改用較短期間的價格報酬資料。",
                ["performance_return_pct"],
            )
            add_warning(
                TargetAnalysisWarningCode
                .INSUFFICIENT_PERFORMANCE_HISTORY,
                "績效歷史未完整涵蓋要求期間。",
                ["performance_return_pct"],
            )

        performance_date = _parse_date(
            selected_performance.get("as_of_date")
        )

        if (
            performance_date is not None
            and is_performance_data_stale(
                performance_date,
                as_of_date,
            )
        ):
            add_warning(
                TargetAnalysisWarningCode
                .STALE_PERFORMANCE_DATA,
                "價格報酬資料已超過更新期限。",
                ["performance_return_pct"],
            )

    return TargetAnalysisData(
        monthly_income=monthly_income,
        dividends=dividends,
        selected_performance=selected_performance,
        warnings=warnings,
        unavailable_fields=unavailable_fields,
    )
