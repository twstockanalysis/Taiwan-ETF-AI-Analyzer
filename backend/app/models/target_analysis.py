from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


from backend.app.models.cash_flow_analysis import (
    CashFlowCalculationResult,
    ScenarioEstimateCalculationResult,
)

class TargetAnalysisStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class TargetAnalysisWarningCode(str, Enum):
    NEGATIVE_TOTAL_RETURN = "NEGATIVE_TOTAL_RETURN"
    PERSISTENT_PRICE_DECLINE = "PERSISTENT_PRICE_DECLINE"
    WEAK_PRICE_RECOVERY = "WEAK_PRICE_RECOVERY"
    MATERIAL_PEER_UNDERPERFORMANCE = (
        "MATERIAL_PEER_UNDERPERFORMANCE"
    )
    INSUFFICIENT_DIVIDEND_HISTORY = (
        "INSUFFICIENT_DIVIDEND_HISTORY"
    )
    INSUFFICIENT_PERFORMANCE_HISTORY = (
        "INSUFFICIENT_PERFORMANCE_HISTORY"
    )
    STALE_DIVIDEND_DATA = "STALE_DIVIDEND_DATA"
    STALE_PERFORMANCE_DATA = "STALE_PERFORMANCE_DATA"
    INCOMPLETE_DIVIDEND_DATA = "INCOMPLETE_DIVIDEND_DATA"
    MIXED_CURRENCY = "MIXED_CURRENCY"
    PERFORMANCE_PERIOD_FALLBACK = "PERFORMANCE_PERIOD_FALLBACK"
    HISTORICAL_RESULTS_NOT_GUARANTEED = (
        "HISTORICAL_RESULTS_NOT_GUARANTEED"
    )


class TargetAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    held_units: int = Field(ge=0)
    unit_price: Decimal = Field(gt=0)
    monthly_after_tax_target: Decimal = Field(ge=0)
    analysis_years: int = Field(ge=1, le=50)
    history_years: int = Field(default=3, ge=1, le=10)
    cash_deduction_rate_pct: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )


class TargetAnalysisWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: TargetAnalysisWarningCode
    message: str = Field(min_length=1)
    affected_fields: list[str] = Field(default_factory=list)
    as_of_date: date | None = None
    source_id: str | None = None
    evidence: dict[str, str | int | Decimal | date | None] = Field(
        default_factory=dict
    )


class TargetAnalysisUnavailableField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class TargetAnalysisMonthlyCashFlow(BaseModel):
    """依歷史付款月份年均化的基礎 ETF 現金流。"""

    model_config = ConfigDict(extra="forbid")

    month: int = Field(ge=1, le=12)
    event_count: int = Field(ge=0)
    observed_year_count: int = Field(ge=0)
    annualized_gross_cash: Decimal | None = Field(default=None, ge=0)
    annualized_after_tax_cash: Decimal | None = Field(default=None, ge=0)
    latest_payment_date: date | None = None

class TargetAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TargetAnalysisStatus

    cash_flow: CashFlowCalculationResult

    scenario_estimate: ScenarioEstimateCalculationResult

    warnings: list[TargetAnalysisWarning] = Field(
        default_factory=list,
    )

    unavailable_fields: list[
        TargetAnalysisUnavailableField
    ] = Field(
        default_factory=list,
    )

    monthly_cash_flow: list[TargetAnalysisMonthlyCashFlow] = Field(
        default_factory=list,
        min_length=0,
        max_length=12,
    )
