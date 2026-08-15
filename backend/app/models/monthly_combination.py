"""M10-5 月配缺口組合與候選排除契約。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class MonthlyCombinationBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


def _normalize_target_months(months: list[int]) -> list[int]:
    normalized = sorted(set(months))
    if not normalized or any(month < 1 or month > 12 for month in normalized):
        raise ValueError("目標付款月份必須介於 1 到 12，且至少選擇一個月份")
    return normalized


class MonthlyCombinationStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class CandidateReasonKind(StrEnum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"
    TRADEOFF = "TRADEOFF"


class CandidateReasonCode(StrEnum):
    PASSES_ELIGIBILITY = "PASSES_ELIGIBILITY"
    SUPPORTS_PAYMENT_MONTHS = "SUPPORTS_PAYMENT_MONTHS"
    MONTHLY_COVERAGE_DISABLED = "MONTHLY_COVERAGE_DISABLED"
    NO_GAP_CONTRIBUTION = "NO_GAP_CONTRIBUTION"
    REDUNDANT_MONTH_COVERAGE = "REDUNDANT_MONTH_COVERAGE"
    INCOMPLETE_DATA = "INCOMPLETE_DATA"
    STALE_DATA = "STALE_DATA"
    UNSTABLE_DISTRIBUTIONS = "UNSTABLE_DISTRIBUTIONS"
    MISSING_TOTAL_RETURN = "MISSING_TOTAL_RETURN"
    WEAK_TOTAL_RETURN = "WEAK_TOTAL_RETURN"
    MISSING_DOWNSIDE_RISK = "MISSING_DOWNSIDE_RISK"
    EXCESSIVE_DOWNSIDE_RISK = "EXCESSIVE_DOWNSIDE_RISK"
    MISSING_AFTER_TAX_CASH = "MISSING_AFTER_TAX_CASH"
    NON_POSITIVE_AFTER_TAX_CASH = "NON_POSITIVE_AFTER_TAX_CASH"
    HOLDING_OVERLAP_UNAVAILABLE = "HOLDING_OVERLAP_UNAVAILABLE"
    EXCESSIVE_HOLDING_OVERLAP = "EXCESSIVE_HOLDING_OVERLAP"
    EXCESSIVE_CONCENTRATION = "EXCESSIVE_CONCENTRATION"
    MAX_COMPLEMENTARY_ETFS_REACHED = "MAX_COMPLEMENTARY_ETFS_REACHED"
    BASE_MONTHLY_DATA_UNAVAILABLE = "BASE_MONTHLY_DATA_UNAVAILABLE"


class CandidateReason(MonthlyCombinationBaseModel):
    kind: CandidateReasonKind
    code: CandidateReasonCode
    message: str = Field(min_length=1)
    affected_months: list[int] = Field(default_factory=list)


class MonthlyCombinationEligibilityRules(MonthlyCombinationBaseModel):
    min_completeness_pct: Decimal = Field(
        default=Decimal("75"), ge=0, le=100
    )
    min_distribution_stability_pct: Decimal = Field(
        default=Decimal("50"), ge=0, le=100
    )
    min_after_tax_total_return_pct: Decimal = Field(
        default=Decimal("0"), ge=-100
    )
    min_downside_return_pct: Decimal = Field(
        default=Decimal("-20"), ge=-100
    )
    max_holding_overlap_pct: Decimal = Field(
        default=Decimal("50"), ge=0, le=100
    )
    max_candidate_allocation_pct: Decimal = Field(
        default=Decimal("20"), gt=0, le=100
    )
    require_holding_overlap: bool = False


class MonthlyCombinationCandidateAssumption(MonthlyCombinationBaseModel):
    etf_code: str = Field(min_length=4, max_length=10)
    unit_price: Decimal = Field(gt=0)
    proposed_allocation_pct: Decimal = Field(gt=0, le=100)
    holding_overlap_pct: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        description="已停用的相容欄位；後端只採用通過品質門檻的自動成分股重疊率。",
    )

    @field_validator("etf_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.upper()


class MonthlyCombinationAnalysisRequest(MonthlyCombinationBaseModel):
    candidates: list[MonthlyCombinationCandidateAssumption] = Field(
        min_length=1, max_length=3
    )
    lookback_years: int = Field(default=3, ge=1, le=10)
    cash_deduction_rate_pct: Decimal = Field(default=0, ge=0, le=100)
    max_complementary_etfs: int = Field(default=3, ge=1, le=3)
    monthly_coverage_enabled: bool = True
    target_payment_months: list[int] = Field(
        default_factory=lambda: list(range(1, 13)),
    )
    rules: MonthlyCombinationEligibilityRules = Field(
        default_factory=MonthlyCombinationEligibilityRules
    )

    @model_validator(mode="after")
    def validate_candidate_codes(self):
        codes = [candidate.etf_code for candidate in self.candidates]
        if len(codes) != len(set(codes)):
            raise ValueError("候選 ETF 代號不可重複")
        if self.max_complementary_etfs > len(codes):
            self.max_complementary_etfs = len(codes)
        self.target_payment_months = _normalize_target_months(
            self.target_payment_months
        )
        return self


class MonthlyCombinationCandidateInput(MonthlyCombinationBaseModel):
    etf_code: str = Field(min_length=4, max_length=10)
    name: str = Field(min_length=1)
    is_active: bool
    is_bond: bool
    stable_payment_months: list[int]
    completeness_pct: Decimal | None = Field(default=None, ge=0, le=100)
    data_is_fresh: bool | None = None
    distribution_stability_pct: Decimal | None = Field(
        default=None, ge=0, le=100
    )
    annual_after_tax_cash_rate_pct: Decimal | None = None
    estimated_after_tax_total_return_pct: Decimal | None = Field(
        default=None, ge=-100
    )
    downside_return_pct: Decimal | None = Field(default=None, ge=-100)
    holding_overlap_pct: Decimal | None = Field(
        default=None, ge=0, le=100
    )
    holding_overlap_is_automatic: bool = False
    proposed_allocation_pct: Decimal = Field(gt=0, le=100)

    @model_validator(mode="after")
    def validate_months(self):
        normalized = sorted(set(self.stable_payment_months))
        if any(month < 1 or month > 12 for month in normalized):
            raise ValueError("付款月份必須介於 1 到 12")
        self.stable_payment_months = normalized
        return self


class MonthlyCombinationCalculationInput(MonthlyCombinationBaseModel):
    base_etf_code: str = Field(min_length=4, max_length=10)
    base_etf_name: str = Field(min_length=1)
    base_payment_months: list[int] | None
    candidates: list[MonthlyCombinationCandidateInput] = Field(
        min_length=1, max_length=20
    )
    max_complementary_etfs: int = Field(default=3, ge=1, le=3)
    monthly_coverage_enabled: bool = True
    target_payment_months: list[int] = Field(
        default_factory=lambda: list(range(1, 13)),
    )
    rules: MonthlyCombinationEligibilityRules = Field(
        default_factory=MonthlyCombinationEligibilityRules
    )

    @model_validator(mode="after")
    def validate_codes_and_months(self):
        codes = [candidate.etf_code for candidate in self.candidates]
        if self.base_etf_code in codes:
            raise ValueError("候選清單不可包含基準 ETF")
        if len(codes) != len(set(codes)):
            raise ValueError("候選 ETF 代號不可重複")
        if self.base_payment_months is not None:
            normalized = sorted(set(self.base_payment_months))
            if any(month < 1 or month > 12 for month in normalized):
                raise ValueError("基準付款月份必須介於 1 到 12")
            self.base_payment_months = normalized
        self.target_payment_months = _normalize_target_months(
            self.target_payment_months
        )
        return self


class MonthlyCombinationCandidateResult(MonthlyCombinationBaseModel):
    etf_code: str
    name: str
    is_active: bool
    is_bond: bool
    selected: bool
    supported_gap_months: list[int]
    stable_payment_months: list[int]
    completeness_pct: Decimal | None
    data_is_fresh: bool | None
    distribution_stability_pct: Decimal | None
    annual_after_tax_cash_rate_pct: Decimal | None
    estimated_after_tax_total_return_pct: Decimal | None
    downside_return_pct: Decimal | None
    holding_overlap_pct: Decimal | None
    holding_overlap_is_automatic: bool = False
    proposed_allocation_pct: Decimal
    reasons: list[CandidateReason]


class MonthlyCombinationCalculationResult(MonthlyCombinationBaseModel):
    status: MonthlyCombinationStatus
    estimate_label: str = "月配組合情境，非投資建議或保證"
    base_etf_code: str
    base_etf_name: str
    base_payment_months: list[int] | None
    target_payment_months: list[int] = Field(min_length=1)
    initial_gap_months: list[int] | None
    selected_candidates: list[MonthlyCombinationCandidateResult]
    rejected_candidates: list[MonthlyCombinationCandidateResult]
    combined_payment_months: list[int] | None
    remaining_gap_months: list[int] | None
    tradeoffs: list[CandidateReason] = Field(default_factory=list)


class MonthlyCombinationHistoricalFacts(MonthlyCombinationBaseModel):
    as_of_date: date
    lookback_years: int
    date_basis: str = "PAYMENT_DATE"
    performance_metric: str = "PRICE_RETURN"


class MonthlyCombinationAnalysisResult(MonthlyCombinationBaseModel):
    historical_facts: MonthlyCombinationHistoricalFacts
    cash_deduction_rate_pct: Decimal
    calculation: MonthlyCombinationCalculationResult
