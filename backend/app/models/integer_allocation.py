"""V3-3 全市場整數股數配置的公開安全契約。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field

from backend.app.models.market_eligibility import MarketEligibilityIndexRequest
from backend.app.models.public_planner import PublicPlannerBaseModel, PublicPlannerIssue


class IntegerAllocationStatus(StrEnum):
    TARGET_MET = "TARGET_MET"
    PARTIAL = "PARTIAL"
    NO_ELIGIBLE_ALLOCATION = "NO_ELIGIBLE_ALLOCATION"
    UNAVAILABLE = "UNAVAILABLE"


class IntegerAllocationOptimality(StrEnum):
    PROVED_OPTIMAL = "PROVED_OPTIMAL"
    BOUNDED_BEST_EFFORT = "BOUNDED_BEST_EFFORT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class IntegerAllocationRequest(MarketEligibilityIndexRequest):
    pass


class IntegerAllocationAddition(PublicPlannerBaseModel):
    etf_code: str
    name: str
    additional_shares: int = Field(gt=0)
    reference_price: Decimal = Field(gt=0)
    reference_price_as_of: date
    reference_price_source_id: str
    estimated_transaction_cost: Decimal = Field(ge=0)
    required_capital: Decimal = Field(gt=0)
    supported_target_months: list[int] = Field(default_factory=list)
    holding_overlap_pct: Decimal | None = Field(default=None, ge=0, le=100)
    constituent_snapshot_dates: list[date] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class IntegerAllocationMonthResult(PublicPlannerBaseModel):
    month: int = Field(ge=1, le=12)
    current_after_tax_cash: Decimal = Field(ge=0)
    added_after_tax_cash: Decimal = Field(ge=0)
    modeled_after_tax_cash: Decimal = Field(ge=0)
    target_after_tax_cash: Decimal = Field(ge=0)
    shortfall: Decimal = Field(ge=0)


class IntegerAllocationHoldingResult(PublicPlannerBaseModel):
    etf_code: str
    existing_shares: int = Field(ge=0)
    additional_shares: int = Field(ge=0)
    resulting_shares: int = Field(gt=0)
    reference_price: Decimal = Field(gt=0)
    resulting_value: Decimal = Field(gt=0)
    allocation_pct: Decimal = Field(ge=0, le=100)


class IntegerAllocationAssumptions(PublicPlannerBaseModel):
    cash_deduction_rate_pct: Decimal = Field(ge=0, le=100)
    transaction_cost_rate_pct: Literal[Decimal("0")] = Decimal("0")
    max_candidate_allocation_pct: Decimal = Field(gt=0, le=100)
    transaction_cost_note: str = "V3-3 尚未納入券商手續費，交易成本固定以 0 元試算。"


class IntegerAllocationResponse(PublicPlannerBaseModel):
    profile_scope: Literal["PUBLIC_STATELESS"] = "PUBLIC_STATELESS"
    request_persisted: Literal[False] = False
    broker_connected: Literal[False] = False
    methodology: Literal["DETERMINISTIC_INTEGER_ALLOCATION_V3_3"] = (
        "DETERMINISTIC_INTEGER_ALLOCATION_V3_3"
    )
    status: IntegerAllocationStatus
    optimality: IntegerAllocationOptimality
    analysis_date: date
    snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    currency: Literal["TWD"] = "TWD"
    target_after_tax_cash_twd: Decimal = Field(ge=0)
    target_months: list[int] = Field(min_length=1, max_length=12)
    assumptions: IntegerAllocationAssumptions
    universe_count: int = Field(ge=0)
    eligible_count: int = Field(ge=0)
    additions: list[IntegerAllocationAddition] = Field(default_factory=list)
    total_required_additional_capital: Decimal = Field(ge=0)
    monthly_results: list[IntegerAllocationMonthResult]
    resulting_holdings: list[IntegerAllocationHoldingResult] = Field(
        default_factory=list
    )
    issues: list[PublicPlannerIssue] = Field(default_factory=list)
    estimate_label: str = (
        "依歷史資料建立的整數股數配置情境，非投資建議、下單指示或未來績效保證"
    )
