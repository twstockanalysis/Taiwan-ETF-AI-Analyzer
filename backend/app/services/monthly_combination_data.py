"""載入歷史月配與績效資料並轉成 M10-5 候選輸入。"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from backend.app.models.monthly_combination import (
    MonthlyCombinationCandidateAssumption,
    MonthlyCombinationCandidateInput,
    MonthlyCombinationEligibilityRules,
)
from backend.app.services.target_analysis_data import (
    is_dividend_data_stale,
    is_performance_data_stale,
)


_PERIODS = ("1M", "3M", "6M", "1Y")
_PERCENT_QUANTUM = Decimal("0.000001")


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _date(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def stable_payment_months(
    monthly_income: dict | None,
    *,
    lookback_years: int,
    minimum_stability_pct: Decimal,
) -> list[int] | None:
    """以觀察年度出現比例判定穩定付款月份。"""

    if monthly_income is None or monthly_income.get("as_of_date") is None:
        return None
    return [
        int(item["month"])
        for item in monthly_income.get("months", [])
        if (
            Decimal(str(item.get("observed_year_count", 0)))
            / Decimal(str(lookback_years))
            * Decimal("100")
        )
        >= minimum_stability_pct
    ]


def build_candidate_input(
    *,
    etf: dict,
    assumption: MonthlyCombinationCandidateAssumption,
    monthly_income: dict | None,
    performance_rows: list[dict],
    lookback_years: int,
    cash_deduction_rate_pct: Decimal,
    rules: MonthlyCombinationEligibilityRules,
    as_of_date: date,
) -> MonthlyCombinationCandidateInput:
    """保留缺值，建立純計算服務需要的候選事實。"""

    rows_by_period = {
        str(row.get("period_code")): row
        for row in performance_rows
        if row.get("metric_code") == "PRICE_RETURN"
        and str(row.get("period_code")) in _PERIODS
    }
    available_signal_count = len(rows_by_period)
    monthly_available = bool(
        monthly_income
        and monthly_income.get("as_of_date") is not None
        and not monthly_income.get("has_mixed_currencies", False)
        and monthly_income.get("total_amount_per_unit") is not None
    )
    if monthly_available:
        available_signal_count += 1
    completeness_pct = (
        Decimal(available_signal_count)
        / Decimal("5")
        * Decimal("100")
    ).quantize(_PERCENT_QUANTUM, rounding=ROUND_HALF_UP)

    payment_date = _date(
        monthly_income.get("as_of_date") if monthly_income else None
    )
    performance_dates = [
        parsed
        for row in rows_by_period.values()
        if (parsed := _date(row.get("as_of_date"))) is not None
    ]
    data_is_fresh = bool(
        payment_date
        and performance_dates
        and not is_dividend_data_stale(payment_date, as_of_date)
        and all(
            not is_performance_data_stale(item, as_of_date)
            for item in performance_dates
        )
    )

    months = stable_payment_months(
        monthly_income,
        lookback_years=lookback_years,
        minimum_stability_pct=rules.min_distribution_stability_pct,
    ) or []
    covered_month_count = (
        int(monthly_income.get("covered_month_count", 0))
        if monthly_income
        else 0
    )
    occurrence_count = (
        int(monthly_income.get("covered_month_occurrence_count", 0))
        if monthly_income
        else 0
    )
    distribution_stability_pct = None
    if covered_month_count > 0:
        distribution_stability_pct = (
            Decimal(occurrence_count)
            / (Decimal(covered_month_count) * Decimal(lookback_years))
            * Decimal("100")
        ).quantize(_PERCENT_QUANTUM, rounding=ROUND_HALF_UP)

    annual_after_tax_cash_rate_pct = None
    if monthly_available:
        annual_amount = (
            _decimal(monthly_income["total_amount_per_unit"])
            / Decimal(lookback_years)
        )
        annual_after_tax_cash_rate_pct = (
            annual_amount
            / assumption.unit_price
            * (Decimal("100") - cash_deduction_rate_pct)
        ).quantize(_PERCENT_QUANTUM, rounding=ROUND_HALF_UP)

    one_year_return = _decimal(
        rows_by_period.get("1Y", {}).get("return_pct")
    )
    estimated_total_return = None
    if one_year_return is not None and annual_after_tax_cash_rate_pct is not None:
        estimated_total_return = (
            one_year_return + annual_after_tax_cash_rate_pct
        ).quantize(_PERCENT_QUANTUM, rounding=ROUND_HALF_UP)

    returns = [
        value
        for row in rows_by_period.values()
        if (value := _decimal(row.get("return_pct"))) is not None
    ]

    return MonthlyCombinationCandidateInput(
        etf_code=etf["code"],
        name=etf["name"],
        is_active=bool(etf["is_active"]),
        is_bond=bool(etf["is_bond"]),
        stable_payment_months=months,
        completeness_pct=completeness_pct,
        data_is_fresh=data_is_fresh,
        distribution_stability_pct=distribution_stability_pct,
        annual_after_tax_cash_rate_pct=annual_after_tax_cash_rate_pct,
        estimated_after_tax_total_return_pct=estimated_total_return,
        downside_return_pct=min(returns) if returns else None,
        holding_overlap_pct=assumption.holding_overlap_pct,
        proposed_allocation_pct=assumption.proposed_allocation_pct,
    )


@dataclass(frozen=True)
class MonthlyCombinationLoadedData:
    base_etf: dict | None
    base_payment_months: list[int] | None
    candidate_etfs: dict[str, dict | None]
    candidates: list[MonthlyCombinationCandidateInput]


def load_monthly_combination_data(
    *,
    base_etf_code: str,
    assumptions: list[MonthlyCombinationCandidateAssumption],
    database_path,
    lookback_years: int,
    cash_deduction_rate_pct: Decimal,
    rules: MonthlyCombinationEligibilityRules,
    as_of_date: date,
) -> MonthlyCombinationLoadedData:
    """從 repository 載入基準與候選 ETF，不把缺值補成零。"""

    from backend.app.repositories.etf_repository import get_etf_by_code
    from backend.app.repositories.monthly_income_repository import (
        build_monthly_income_distribution,
    )
    from backend.app.repositories.performance_repository import (
        list_latest_etf_performance,
    )

    base_etf = get_etf_by_code(base_etf_code, database_path)
    base_monthly = (
        build_monthly_income_distribution(
            base_etf_code,
            database_path,
            lookback_years,
        )
        if base_etf is not None
        else None
    )
    base_payment_months = stable_payment_months(
        base_monthly,
        lookback_years=lookback_years,
        minimum_stability_pct=rules.min_distribution_stability_pct,
    )

    candidate_etfs: dict[str, dict | None] = {}
    candidates: list[MonthlyCombinationCandidateInput] = []
    for assumption in assumptions:
        etf = get_etf_by_code(assumption.etf_code, database_path)
        candidate_etfs[assumption.etf_code] = etf
        if etf is None:
            continue
        monthly_income = build_monthly_income_distribution(
            assumption.etf_code,
            database_path,
            lookback_years,
        )
        performance_rows = list_latest_etf_performance(
            assumption.etf_code,
            database_path,
        )
        candidates.append(
            build_candidate_input(
                etf=etf,
                assumption=assumption,
                monthly_income=monthly_income,
                performance_rows=performance_rows,
                lookback_years=lookback_years,
                cash_deduction_rate_pct=cash_deduction_rate_pct,
                rules=rules,
                as_of_date=as_of_date,
            )
        )

    return MonthlyCombinationLoadedData(
        base_etf=base_etf,
        base_payment_months=base_payment_months,
        candidate_etfs=candidate_etfs,
        candidates=candidates,
    )
