"""V3-1 公開且不持久化的現金流試算契約。"""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PublicPlannerBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PublicPlannerStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class PublicPlannerHoldingInput(PublicPlannerBaseModel):
    etf_code: str = Field(min_length=1, max_length=10)
    held_units: int = Field(gt=0, le=1_000_000_000_000)

    @field_validator("etf_code", mode="before")
    @classmethod
    def normalize_etf_code(cls, value: object) -> str:
        if not isinstance(value, str):
            raise TypeError("ETF 代號必須是文字")
        return value.strip().upper()


class PublicPlannerRequest(PublicPlannerBaseModel):
    target_after_tax_cash_twd: Decimal = Field(
        ge=0,
        max_digits=18,
        decimal_places=6,
    )
    target_months: list[int] = Field(min_length=1, max_length=12)
    existing_holdings: list[PublicPlannerHoldingInput] = Field(
        default_factory=list,
        max_length=500,
    )
    history_years: int = Field(default=3, ge=1, le=10)
    cash_deduction_rate_pct: Decimal = Field(default=0, ge=0, le=100)
    currency: Literal["TWD"] = "TWD"

    @field_validator("target_months")
    @classmethod
    def normalize_target_months(cls, value: list[int]) -> list[int]:
        normalized = sorted(set(value))
        if not normalized or any(month < 1 or month > 12 for month in normalized):
            raise ValueError("目標月份必須介於 1 到 12，且至少選擇一個月份")
        return normalized

    @model_validator(mode="after")
    def reject_duplicate_holdings(self):
        codes = [holding.etf_code for holding in self.existing_holdings]
        if len(codes) != len(set(codes)):
            raise ValueError("現有持股不可包含重複 ETF 代號")
        return self


class PublicPlannerIssue(PublicPlannerBaseModel):
    code: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1)
    field: str | None = None
    etf_code: str | None = None


class PublicPlannerHoldingFact(PublicPlannerBaseModel):
    etf_code: str
    name: str
    held_units: int = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, gt=0)
    price_as_of_date: date | None = None
    price_source_id: str | None = None
    current_value: Decimal | None = Field(default=None, gt=0)
    historical_payment_months: list[int] = Field(default_factory=list)
    issues: list[PublicPlannerIssue] = Field(default_factory=list)


class PublicPlannerMonthResult(PublicPlannerBaseModel):
    month: int = Field(ge=1, le=12)
    selected: bool
    gross_cash: Decimal | None = Field(default=None, ge=0)
    after_tax_cash: Decimal | None = Field(default=None, ge=0)
    target_after_tax_cash: Decimal = Field(ge=0)
    shortfall: Decimal | None = Field(default=None, ge=0)


class PublicPlannerResponse(PublicPlannerBaseModel):
    profile_scope: Literal["PUBLIC_STATELESS"] = "PUBLIC_STATELESS"
    request_persisted: Literal[False] = False
    broker_connected: Literal[False] = False
    methodology: Literal["PUBLIC_BASELINE_V3_1"] = "PUBLIC_BASELINE_V3_1"
    status: PublicPlannerStatus
    analysis_date: date
    currency: Literal["TWD"] = "TWD"
    target_after_tax_cash_twd: Decimal = Field(ge=0)
    target_months: list[int] = Field(min_length=1, max_length=12)
    history_years: int = Field(ge=1, le=10)
    cash_deduction_rate_pct: Decimal = Field(ge=0, le=100)
    total_current_value: Decimal | None = Field(default=None, ge=0)
    holdings: list[PublicPlannerHoldingFact] = Field(default_factory=list)
    monthly_cash_flow: list[PublicPlannerMonthResult] = Field(
        min_length=12,
        max_length=12,
    )
    issues: list[PublicPlannerIssue] = Field(default_factory=list)
    next_step: Literal["AUTO_ALLOCATION_PENDING"] = "AUTO_ALLOCATION_PENDING"
    estimate_label: str = "現有持股歷史現金流基線，非投資建議或未來配息保證"
