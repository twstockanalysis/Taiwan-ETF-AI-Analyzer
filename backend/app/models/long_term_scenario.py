"""V3-5 組合含息績效與長期情境公開契約。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field

from backend.app.models.allocation_results import (
    AllocationResultsRequest,
    AllocationResultsResponse,
    AllocationStrategy,
)
from backend.app.models.public_planner import PublicPlannerBaseModel, PublicPlannerIssue


class HistoricalEvidenceStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class HistoricalPeriod(StrEnum):
    AVAILABLE_HISTORY = "AVAILABLE_HISTORY"
    THREE_YEARS = "3Y"
    FIVE_YEARS = "5Y"
    TEN_YEARS = "10Y"


class ScenarioBand(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    BASE = "BASE"
    OPTIMISTIC = "OPTIMISTIC"


class HistoricalPortfolioEvidence(PublicPlannerBaseModel):
    period: HistoricalPeriod
    status: HistoricalEvidenceStatus
    price_basis: Literal["RAW_OFFICIAL_CLOSE"] = "RAW_OFFICIAL_CLOSE"
    distribution_policy: Literal["NO_REINVESTMENT"] = "NO_REINVESTMENT"
    period_start: date | None = None
    period_end: date | None = None
    observation_days: int | None = Field(default=None, ge=0)
    start_value: Decimal | None = Field(default=None, ge=0)
    end_value: Decimal | None = Field(default=None, ge=0)
    gross_distributions: Decimal | None = Field(default=None, ge=0)
    after_deduction_distributions: Decimal | None = Field(default=None, ge=0)
    total_return_pct: Decimal | None = Field(default=None, ge=-100)
    annualized_total_return_pct: Decimal | None = Field(default=None, ge=-100)
    issues: list[PublicPlannerIssue] = Field(default_factory=list)


class ScenarioIndexPoint(PublicPlannerBaseModel):
    year: int = Field(ge=0, le=10)
    total_value_index: Decimal = Field(ge=0)


class LongTermScenarioBand(PublicPlannerBaseModel):
    band: ScenarioBand
    label: str
    annual_total_return_assumption_pct: Decimal = Field(ge=-100)
    percentile: Decimal = Field(ge=0, le=100)
    projection_years: Literal[10] = 10
    calculation_basis: Literal["COMPOUNDED_TOTAL_RETURN_INDEX"] = (
        "COMPOUNDED_TOTAL_RETURN_INDEX"
    )
    index_points: list[ScenarioIndexPoint] = Field(min_length=11, max_length=11)


class AllocationPlanLongTermEvidence(PublicPlannerBaseModel):
    strategy: AllocationStrategy
    historical_periods: list[HistoricalPortfolioEvidence] = Field(
        min_length=4,
        max_length=4,
    )
    annual_observation_count: int = Field(ge=0)
    scenarios: list[LongTermScenarioBand] = Field(default_factory=list, max_length=3)
    issues: list[PublicPlannerIssue] = Field(default_factory=list)


class LongTermScenarioRequest(AllocationResultsRequest):
    pass


class LongTermScenarioResponse(PublicPlannerBaseModel):
    profile_scope: Literal["PUBLIC_STATELESS"] = "PUBLIC_STATELESS"
    request_persisted: Literal[False] = False
    broker_connected: Literal[False] = False
    methodology: Literal["PORTFOLIO_LONG_TERM_SCENARIO_V3_5"] = (
        "PORTFOLIO_LONG_TERM_SCENARIO_V3_5"
    )
    allocation_results: AllocationResultsResponse
    plan_evidence: list[AllocationPlanLongTermEvidence] = Field(min_length=1)
    estimate_label: str = (
        "歷史含息績效與十年情境試算，非未來預測、投資建議或績效保證"
    )
