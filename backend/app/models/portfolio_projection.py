"""V3-6 整體組合稅務與再投入公開契約。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field

from backend.app.models.allocation_results import AllocationStrategy
from backend.app.models.long_term_scenario import (
    LongTermScenarioRequest,
    LongTermScenarioResponse,
    ScenarioBand,
)
from backend.app.models.public_planner import PublicPlannerBaseModel, PublicPlannerIssue
from backend.app.models.tax_reinvestment import (
    ComponentCalculationBasis,
    OfficialComponentAllocation,
    ReinvestmentPolicy,
)


class DividendTaxMethod(StrEnum):
    COMBINED_WITH_CREDIT = "COMBINED_WITH_CREDIT"
    SEPARATE_28 = "SEPARATE_28"


class PortfolioProjectionStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class PortfolioProjectionRequest(LongTermScenarioRequest):
    projection_years: int = Field(default=10, ge=1, le=20)
    custom_reinvestment_pct: Decimal = Field(default=50, ge=0, le=100)
    dividend_tax_method: DividendTaxMethod = DividendTaxMethod.COMBINED_WITH_CREDIT
    marginal_income_tax_rate_pct: Decimal = Field(default=5, ge=0, le=100)
    other_income_tax_rate_pct: Decimal = Field(default=0, ge=0, le=100)
    remaining_annual_dividend_credit_cap_twd: Decimal = Field(
        default=80000,
        ge=0,
        le=80000,
    )
    supplementary_premium_exempt: bool = False


class PortfolioHoldingTaxFact(PublicPlannerBaseModel):
    etf_code: str
    units: Decimal = Field(gt=0)
    initial_unit_price: Decimal = Field(gt=0)
    initial_value: Decimal = Field(gt=0)
    history_start_date: date | None = None
    history_end_date: date | None = None
    annual_gross_distribution_rate_pct: Decimal | None = Field(default=None, ge=0)
    annual_gross_distribution_cash: Decimal | None = Field(default=None, ge=0)
    estimated_payments_per_year: int | None = Field(default=None, ge=1)
    component_calculation_basis: ComponentCalculationBasis | None = None
    component_source_event_id: str | None = None
    component_source_date: date | None = None
    calculation_component_mix: list[OfficialComponentAllocation] | None = None
    issues: list[PublicPlannerIssue] = Field(default_factory=list)


class PortfolioProjectionYearPoint(PublicPlannerBaseModel):
    year: int = Field(ge=0, le=20)
    ending_value: Decimal = Field(ge=0)
    usable_cash: Decimal = Field(ge=0)
    reinvested_cash: Decimal = Field(ge=0)
    modeled_income_tax: Decimal = Field(ge=0)
    modeled_supplementary_premium: Decimal = Field(ge=0)


class PortfolioReinvestmentResult(PublicPlannerBaseModel):
    policy: ReinvestmentPolicy
    custom_reinvestment_pct: Decimal | None = Field(default=None, ge=0, le=100)
    usable_cash: Decimal = Field(ge=0)
    reinvested_cash: Decimal = Field(ge=0)
    ending_value: Decimal = Field(ge=0)
    modeled_income_tax: Decimal = Field(ge=0)
    modeled_supplementary_premium: Decimal = Field(ge=0)
    modeled_tax_cost: Decimal = Field(ge=0)
    after_tax_total_gain_loss: Decimal
    after_tax_total_return_pct: Decimal = Field(ge=-100)
    year_points: list[PortfolioProjectionYearPoint] = Field(min_length=2, max_length=21)


class PortfolioMarketProjection(PublicPlannerBaseModel):
    band: ScenarioBand
    label: str
    gross_annual_total_return_assumption_pct: Decimal = Field(ge=-100)
    derived_annual_price_return_pct: Decimal = Field(ge=-100)
    reinvestment_results: list[PortfolioReinvestmentResult] = Field(
        min_length=4,
        max_length=4,
    )


class AllocationPlanPortfolioProjection(PublicPlannerBaseModel):
    strategy: AllocationStrategy
    status: PortfolioProjectionStatus
    initial_value: Decimal = Field(ge=0)
    annual_cash_target: Decimal = Field(ge=0)
    weighted_annual_gross_distribution_rate_pct: Decimal | None = Field(
        default=None,
        ge=0,
    )
    official_54c_annual_cash: Decimal | None = Field(default=None, ge=0)
    official_76w_annual_cash: Decimal | None = Field(default=None, ge=0)
    actual_component_holding_count: int = Field(ge=0)
    estimated_component_holding_count: int = Field(ge=0)
    unavailable_component_holding_count: int = Field(ge=0)
    holding_facts: list[PortfolioHoldingTaxFact] = Field(default_factory=list)
    market_projections: list[PortfolioMarketProjection] = Field(default_factory=list)
    issues: list[PublicPlannerIssue] = Field(default_factory=list)


class PortfolioProjectionResponse(PublicPlannerBaseModel):
    profile_scope: Literal["PUBLIC_STATELESS"] = "PUBLIC_STATELESS"
    request_persisted: Literal[False] = False
    broker_connected: Literal[False] = False
    methodology: Literal["PORTFOLIO_TAX_REINVESTMENT_V3_6"] = (
        "PORTFOLIO_TAX_REINVESTMENT_V3_6"
    )
    currency: Literal["TWD"] = "TWD"
    projection_years: int = Field(ge=1, le=20)
    tax_rule_version: Literal["TW-INDIVIDUAL-2026.2"] = "TW-INDIVIDUAL-2026.2"
    tax_rule_verified_date: date = date(2026, 8, 25)
    supplementary_premium_rate_pct: Literal[Decimal("2.11")] = Decimal("2.11")
    supplementary_premium_payment_threshold_twd: Literal[Decimal("20000")] = (
        Decimal("20000")
    )
    supplementary_premium_payment_cap_twd: Literal[Decimal("10000000")] = (
        Decimal("10000000")
    )
    dividend_tax_method: DividendTaxMethod
    long_term_scenarios: LongTermScenarioResponse
    plan_projections: list[AllocationPlanPortfolioProjection] = Field(min_length=1)
    estimate_label: str = (
        "整體組合稅務與再投入情境估算，非稅務建議、投資建議或績效保證"
    )
