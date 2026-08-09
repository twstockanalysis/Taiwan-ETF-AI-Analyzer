"""M11-1 單一使用者條件與手動持有部位契約。"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
