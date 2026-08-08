from decimal import Decimal

from backend.app.models.cash_flow_analysis import (
    CalculationContext,
    CashFlowCalculationInput,
    ScenarioEstimateCalculationInput,
)
from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
    TargetAnalysisResult,
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
    TargetAnalysisWarning,
    TargetAnalysisWarningCode,
)
from backend.app.services.cash_flow_calculator import (
    calculate_cash_flow_target,
    calculate_scenario_estimate,
)


def calculate_current_holding_value(
    request: TargetAnalysisRequest,
) -> Decimal:
    """Calculate the current market value of the held units."""
    return request.unit_price * request.held_units


def build_cash_flow_calculation_input(
    request: TargetAnalysisRequest,
    *,
    context: CalculationContext,
    gross_distribution_cash: Decimal | str | None,
    distribution_tax: Decimal | str | None,
    supplementary_premium: Decimal | str | None,
    other_distribution_costs: Decimal | str | None,
) -> CashFlowCalculationInput:
    """Map target-analysis values to cash-flow input."""
    current_holding_value = calculate_current_holding_value(
        request
    )

    return CashFlowCalculationInput(
        context=context,
        available_capital=current_holding_value,
        monthly_after_tax_target=(
            request.monthly_after_tax_target
        ),
        reference_capital=current_holding_value,
        gross_distribution_cash=gross_distribution_cash,
        distribution_tax=distribution_tax,
        supplementary_premium=supplementary_premium,
        other_distribution_costs=other_distribution_costs,
    )

def build_scenario_estimate_input(
    request: TargetAnalysisRequest,
    *,
    context: CalculationContext,
    annual_gross_cash_rate_pct: Decimal | str | None,
    annual_price_return_pct: Decimal | str | None,
) -> ScenarioEstimateCalculationInput:
    """Map a target-analysis request to scenario-estimate input."""
    return ScenarioEstimateCalculationInput(
        context=context,
        initial_capital=calculate_current_holding_value(
            request
        ),
        annual_gross_cash_rate_pct=(
            annual_gross_cash_rate_pct
        ),
        cash_deduction_rate_pct=(
            request.cash_deduction_rate_pct
        ),
        annual_price_return_pct=(
            annual_price_return_pct
        ),
        projection_years=request.analysis_years,
    )

def _collect_unavailable_fields(
    *results: object,
) -> list[TargetAnalysisUnavailableField]:
    """Map calculator issues to target-analysis fields."""
    unavailable_fields: list[
        TargetAnalysisUnavailableField
    ] = []
    seen_fields: set[str] = set()

    for result in results:
        for issue in getattr(result, "issues", []):
            if issue.field in seen_fields:
                continue

            seen_fields.add(issue.field)
            unavailable_fields.append(
                TargetAnalysisUnavailableField(
                    field=issue.field,
                    reason=issue.reason.value,
                )
            )

    return unavailable_fields


def _build_qualification_warnings(
    *,
    unavailable_fields: list[
        TargetAnalysisUnavailableField
    ],
    gross_distribution_cash: Decimal | str | None,
    distribution_tax: Decimal | str | None,
    supplementary_premium: Decimal | str | None,
    other_distribution_costs: Decimal | str | None,
    annual_gross_cash_rate_pct: Decimal | str | None,
    annual_price_return_pct: Decimal | str | None,
) -> list[TargetAnalysisWarning]:
    """Describe missing historical inputs at the API boundary."""
    if not unavailable_fields:
        return []

    unavailable_names = {
        unavailable.field
        for unavailable in unavailable_fields
    }
    warnings: list[TargetAnalysisWarning] = []

    dividend_fields = [
        field
        for field in (
            "after_tax_usable_cash",
            "target_coverage_pct",
            "required_capital",
            "funding_shortfall",
            "cumulative_gross_cash",
            "cumulative_cash_deductions",
            "cumulative_after_tax_cash",
            "after_tax_total_gain_loss",
            "after_tax_total_return_pct",
        )
        if field in unavailable_names
    ]

    if (
        gross_distribution_cash is None
        or annual_gross_cash_rate_pct is None
    ):
        warnings.append(
            TargetAnalysisWarning(
                code=(
                    TargetAnalysisWarningCode
                    .INSUFFICIENT_DIVIDEND_HISTORY
                ),
                message=(
                    "Dividend history is insufficient "
                    "for part of the analysis."
                ),
                affected_fields=dividend_fields,
            )
        )
    elif any(
        value is None
        for value in (
            distribution_tax,
            supplementary_premium,
            other_distribution_costs,
        )
    ):
        warnings.append(
            TargetAnalysisWarning(
                code=(
                    TargetAnalysisWarningCode
                    .INCOMPLETE_DIVIDEND_DATA
                ),
                message=(
                    "Dividend data is incomplete "
                    "for part of the analysis."
                ),
                affected_fields=dividend_fields,
            )
        )

    if annual_price_return_pct is None:
        performance_fields = [
            field
            for field in (
                "ending_holding_value",
                "after_tax_total_gain_loss",
                "after_tax_total_return_pct",
            )
            if field in unavailable_names
        ]
        warnings.append(
            TargetAnalysisWarning(
                code=(
                    TargetAnalysisWarningCode
                    .INSUFFICIENT_PERFORMANCE_HISTORY
                ),
                message=(
                    "Performance history is insufficient "
                    "for part of the analysis."
                ),
                affected_fields=performance_fields,
            )
        )

    return warnings

def calculate_target_analysis(
    request: TargetAnalysisRequest,
    *,
    context: CalculationContext,
    gross_distribution_cash: Decimal | str | None,
    distribution_tax: Decimal | str | None,
    supplementary_premium: Decimal | str | None,
    other_distribution_costs: Decimal | str | None,
    annual_gross_cash_rate_pct: Decimal | str | None,
    annual_price_return_pct: Decimal | str | None,
) -> TargetAnalysisResult:
    """Run the existing calculators and assemble target analysis."""
    cash_flow_input = build_cash_flow_calculation_input(
        request,
        context=context,
        gross_distribution_cash=gross_distribution_cash,
        distribution_tax=distribution_tax,
        supplementary_premium=supplementary_premium,
        other_distribution_costs=other_distribution_costs,
    )
    scenario_input = build_scenario_estimate_input(
        request,
        context=context,
        annual_gross_cash_rate_pct=annual_gross_cash_rate_pct,
        annual_price_return_pct=annual_price_return_pct,
    )

    cash_flow_result = calculate_cash_flow_target(
        cash_flow_input
    )
    scenario_result = calculate_scenario_estimate(
        scenario_input
    )

    unavailable_fields = _collect_unavailable_fields(
        cash_flow_result,
        scenario_result,
    )
    warnings = _build_qualification_warnings(
        unavailable_fields=unavailable_fields,
        gross_distribution_cash=gross_distribution_cash,
        distribution_tax=distribution_tax,
        supplementary_premium=supplementary_premium,
        other_distribution_costs=other_distribution_costs,
        annual_gross_cash_rate_pct=(
            annual_gross_cash_rate_pct
        ),
        annual_price_return_pct=annual_price_return_pct,
    )

    return TargetAnalysisResult(
        status=(
            TargetAnalysisStatus.PARTIAL
            if unavailable_fields
            else TargetAnalysisStatus.AVAILABLE
        ),
        cash_flow=cash_flow_result,
        scenario_estimate=scenario_result,
        warnings=warnings,
        unavailable_fields=unavailable_fields,
    )
