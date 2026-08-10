"""M11-1 單一使用者條件與手動持有部位契約。"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.target_analysis import (
    TargetAnalysisResult,
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
    TargetAnalysisWarning,
)
from backend.app.models.monthly_combination import (
    MonthlyCombinationCalculationResult,
    MonthlyCombinationEligibilityRules,
)


class DecisionProfileBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class UserConditionsUpsert(DecisionProfileBaseModel):
    monthly_after_tax_target: Decimal = Field(ge=0)
    analysis_years: int = Field(ge=1, le=50)
    history_years: int = Field(default=3, ge=1, le=10)
    cash_deduction_rate_pct: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    currency: Literal["TWD"] = "TWD"


class UserConditionsResponse(UserConditionsUpsert):
    updated_at: datetime


class ManualHoldingUpsert(DecisionProfileBaseModel):
    held_units: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    price_as_of_date: date | None = None
    currency: Literal["TWD"] = "TWD"

    @field_validator("price_as_of_date")
    @classmethod
    def reject_future_price_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("參考價格日期不可晚於今天")
        return value


class ManualHoldingResponse(ManualHoldingUpsert):
    etf_code: str
    name: str
    is_active: bool
    is_bond: bool
    updated_at: datetime


class DecisionProfileResponse(DecisionProfileBaseModel):
    profile_scope: Literal["SINGLE_USER"] = "SINGLE_USER"
    broker_connected: Literal[False] = False
    conditions: UserConditionsResponse | None
    holdings: list[ManualHoldingResponse]


class CurrentHoldingFact(DecisionProfileBaseModel):
    """單一手動持倉對整體分析提供的歷史事實。"""

    etf_code: str
    name: str
    held_units: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    current_value: Decimal = Field(gt=0)
    annual_gross_distribution_cash: Decimal | None = Field(
        default=None,
        ge=0,
    )
    price_return_period_code: str | None = None
    annualized_price_return_pct: Decimal | None = Field(
        default=None,
        ge=-100,
    )
    warnings: list[TargetAnalysisWarning] = Field(default_factory=list)
    unavailable_fields: list[TargetAnalysisUnavailableField] = Field(
        default_factory=list,
    )


class CurrentHoldingAnalysisResponse(DecisionProfileBaseModel):
    """以已儲存條件分析整體手動持倉的唯讀結果。"""

    profile_scope: Literal["SINGLE_USER"] = "SINGLE_USER"
    broker_connected: Literal[False] = False
    status: TargetAnalysisStatus
    analysis_date: date
    currency: Literal["TWD"] = "TWD"
    conditions: UserConditionsResponse | None
    total_current_value: Decimal | None = Field(default=None, ge=0)
    holdings: list[CurrentHoldingFact] = Field(default_factory=list)
    portfolio_analysis: TargetAnalysisResult | None = None
    unavailable_fields: list[TargetAnalysisUnavailableField] = Field(
        default_factory=list,
    )


class CandidateHoldingAnalysisRequest(DecisionProfileBaseModel):
    """不寫入持倉的候選 ETF 加碼假設。"""

    proposed_units: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    holding_overlap_pct: Decimal | None = Field(default=None, ge=0, le=100)
    monthly_coverage_enabled: bool = True
    rules: MonthlyCombinationEligibilityRules = Field(
        default_factory=MonthlyCombinationEligibilityRules,
    )


class CandidatePortfolioComparison(DecisionProfileBaseModel):
    """候選加入前後可直接比較的投資組合欄位。"""

    additional_capital: Decimal = Field(gt=0)
    total_value_before: Decimal
    total_value_after: Decimal
    annual_after_tax_cash_before: Decimal | None = None
    annual_after_tax_cash_after: Decimal | None = None
    annual_after_tax_cash_delta: Decimal | None = None
    target_coverage_pct_before: Decimal | None = None
    target_coverage_pct_after: Decimal | None = None
    target_coverage_pct_delta: Decimal | None = None
    funding_shortfall_before: Decimal | None = None
    funding_shortfall_after: Decimal | None = None
    funding_shortfall_reduction: Decimal | None = None
    after_tax_total_return_pct_before: Decimal | None = None
    after_tax_total_return_pct_after: Decimal | None = None
    after_tax_total_return_pct_delta: Decimal | None = None


class CandidateHoldingAnalysisResponse(DecisionProfileBaseModel):
    """M11-3 候選 ETF 對目前持倉的唯讀情境比較。"""

    profile_scope: Literal["SINGLE_USER"] = "SINGLE_USER"
    broker_connected: Literal[False] = False
    status: TargetAnalysisStatus
    analysis_date: date
    estimate_label: str = "候選 ETF 加碼情境，非投資建議或保證"
    candidate_etf_code: str
    candidate_name: str
    current_portfolio: CurrentHoldingAnalysisResponse | None = None
    proposed_portfolio: CurrentHoldingAnalysisResponse | None = None
    comparison: CandidatePortfolioComparison | None = None
    eligibility: MonthlyCombinationCalculationResult | None = None
    decision_priority: list[str] = Field(
        default_factory=lambda: [
            "TOTAL_RETURN_AND_PRINCIPAL_RISK",
            "AFTER_TAX_CASH_FLOW_FEASIBILITY",
            "TAX_EFFICIENCY",
            "OPTIONAL_MONTHLY_PAYMENT_COVERAGE",
        ]
    )
    unavailable_fields: list[TargetAnalysisUnavailableField] = Field(
        default_factory=list,
    )


class DecisionRecordNote(DecisionProfileBaseModel):
    """可匯出且可追溯的決策紀錄說明。"""

    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1)
    affected_months: list[int] = Field(default_factory=list)


DecisionRecordOutcome = Literal[
    "ELIGIBLE",
    "INELIGIBLE",
    "NOT_EVALUATED",
    "UNAVAILABLE",
]


class DecisionRecordSummary(DecisionProfileBaseModel):
    """不可變候選評估快照的列表摘要。"""

    id: int = Field(gt=0)
    record_type: Literal["CANDIDATE_HOLDING_ANALYSIS"]
    candidate_etf_code: str
    candidate_name: str
    analysis_status: TargetAnalysisStatus
    outcome: DecisionRecordOutcome
    created_at: datetime


class DecisionRecordResponse(DecisionRecordSummary):
    """包含輸入、分析與理由的完整不可變決策快照。"""

    profile_scope: Literal["SINGLE_USER"] = "SINGLE_USER"
    broker_connected: Literal[False] = False
    immutable: Literal[True] = True
    request: CandidateHoldingAnalysisRequest
    analysis: CandidateHoldingAnalysisResponse
    rationale: list[DecisionRecordNote] = Field(default_factory=list)
    exclusions: list[DecisionRecordNote] = Field(default_factory=list)
    alternatives: list[DecisionRecordNote] = Field(default_factory=list)
    risk_notes: list[DecisionRecordNote] = Field(default_factory=list)
