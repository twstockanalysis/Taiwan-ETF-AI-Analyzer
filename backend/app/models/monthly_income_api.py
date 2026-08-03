"""每月領息分布 API 資料模型。"""

from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class MonthlyIncomeAPIBaseModel(BaseModel):
    """每月領息 API 回應模型共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
    )


class MonthlyIncomeMonthItem(
    MonthlyIncomeAPIBaseModel
):
    """單一曆月的歷史入帳分布。"""

    month: int = Field(
        ge=1,
        le=12,
    )

    event_count: int = Field(
        ge=0,
    )

    observed_year_count: int = Field(
        ge=0,
    )

    total_amount_per_unit: (
        float | None
    ) = Field(
        default=None,
        ge=0,
    )

    average_amount_per_event: (
        float | None
    ) = Field(
        default=None,
        ge=0,
    )

    latest_payment_date: date | None = None


class MonthlyIncomeDistributionResponse(
    MonthlyIncomeAPIBaseModel
):
    """單一 ETF 的每月領息分布。"""

    etf_code: str = Field(
        min_length=1,
        max_length=10,
    )

    name: str = Field(
        min_length=1,
    )

    date_basis: Literal["PAYMENT_DATE"]

    lookback_years: int = Field(
        ge=1,
        le=10,
    )

    as_of_date: date | None = None

    window_start_date: date | None = None

    total_dividend_event_count: int = Field(
        ge=0,
    )

    dated_dividend_event_count: int = Field(
        ge=0,
    )

    missing_payment_date_count: int = Field(
        ge=0,
    )

    analysis_event_count: int = Field(
        ge=0,
    )

    covered_month_count: int = Field(
        ge=0,
        le=12,
    )

    covered_month_occurrence_count: int = Field(
        ge=0,
    )

    analysis_currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )

    has_mixed_currencies: bool

    total_amount_per_unit: (
        float | None
    ) = Field(
        default=None,
        ge=0,
    )

    months: list[MonthlyIncomeMonthItem] = Field(
        min_length=12,
        max_length=12,
    )
