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
