"""V3-2 全市場候選資格索引的公開安全契約。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field

from backend.app.models.public_planner import (
    PublicPlannerBaseModel,
    PublicPlannerRequest,
)
from backend.app.models.quality_grade import ETFHistoricalQualityGrade


class MarketEligibilityReasonKind(StrEnum):
    EXCLUDE = "EXCLUDE"
    TRADEOFF = "TRADEOFF"


class MarketEligibilityReason(PublicPlannerBaseModel):
    kind: MarketEligibilityReasonKind
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1)


class MarketEligibilityRules(PublicPlannerBaseModel):
    min_completeness_pct: Decimal = Field(default=Decimal("75"), ge=0, le=100)
    min_distribution_stability_pct: Decimal = Field(
        default=Decimal("50"), ge=0, le=100
    )
    min_after_tax_total_return_pct: Decimal = Field(
        default=Decimal("0"), ge=-100
    )
    min_downside_return_pct: Decimal = Field(default=Decimal("-20"), ge=-100)
    max_holding_overlap_pct: Decimal = Field(
        default=Decimal("50"), ge=0, le=100
    )
    max_candidate_allocation_pct: Decimal = Field(
        default=Decimal("20"), gt=0, le=100
    )
    max_reference_price_age_days: int = Field(default=10, ge=0, le=31)


class MarketEligibilityIndexRequest(PublicPlannerRequest):
    pass


class MarketEligibilityItem(PublicPlannerBaseModel):
    etf_code: str
    name: str
    is_active: bool
    is_bond: bool
    existing_holding: bool
    supported_product: bool
    eligible_for_addition: bool
    historical_quality_grade: ETFHistoricalQualityGrade
    reference_price: Decimal | None = Field(default=None, gt=0)
    reference_price_as_of: date | None = None
    reference_price_source_id: str | None = None
    performance_as_of: dict[str, date | None] = Field(default_factory=dict)
    latest_payment_date: date | None = None
    stable_payment_months: list[int] = Field(default_factory=list)
    completeness_pct: Decimal | None = Field(default=None, ge=0, le=100)
    data_is_fresh: bool | None = None
    distribution_stability_pct: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    annual_after_tax_cash_rate_pct: Decimal | None = None
    estimated_after_tax_total_return_pct: Decimal | None = Field(
        default=None,
        ge=-100,
    )
    downside_return_pct: Decimal | None = Field(default=None, ge=-100)
    component_basis: Literal["ACTUAL", "ESTIMATED_FALLBACK"] | None = None
    component_source_date: date | None = None
    actual_76w_available: bool = False
    holding_overlap_status: Literal["AVAILABLE", "NOT_APPLICABLE", "UNAVAILABLE"]
    holding_overlap_pct: Decimal | None = Field(default=None, ge=0, le=100)
    constituent_snapshot_dates: list[date] = Field(default_factory=list)
    reasons: list[MarketEligibilityReason] = Field(default_factory=list)


class MarketEligibilityConstraint(PublicPlannerBaseModel):
    code: Literal["MAX_CANDIDATE_ALLOCATION_PCT"] = "MAX_CANDIDATE_ALLOCATION_PCT"
    value: Decimal = Field(gt=0, le=100)
    enforcement_stage: Literal["V3_3_INTEGER_ALLOCATION"] = (
        "V3_3_INTEGER_ALLOCATION"
    )


class MarketEligibilityIndexResponse(PublicPlannerBaseModel):
    profile_scope: Literal["PUBLIC_STATELESS"] = "PUBLIC_STATELESS"
    request_persisted: Literal[False] = False
    methodology: Literal["DETERMINISTIC_MARKET_ELIGIBILITY_V3_2"] = (
        "DETERMINISTIC_MARKET_ELIGIBILITY_V3_2"
    )
    analysis_date: date
    snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    target_months: list[int] = Field(min_length=1, max_length=12)
    history_years: int = Field(ge=1, le=10)
    cash_deduction_rate_pct: Decimal = Field(ge=0, le=100)
    rules: MarketEligibilityRules
    universe_count: int = Field(ge=0)
    supported_product_count: int = Field(ge=0)
    eligible_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    actual_component_count: int = Field(ge=0)
    estimated_component_fallback_count: int = Field(ge=0)
    allocation_constraints: list[MarketEligibilityConstraint]
    candidates: list[MarketEligibilityItem]
    next_step: Literal["INTEGER_ALLOCATION_PENDING"] = "INTEGER_ALLOCATION_PENDING"
    estimate_label: str = "全市場歷史資料資格索引，非投資建議或未來績效保證"
