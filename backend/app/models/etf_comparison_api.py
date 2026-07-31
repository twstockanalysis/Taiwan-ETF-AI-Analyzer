"""ETF 多檔比較 API 回應模型。"""

from datetime import date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from backend.app.models.etf import ETFResponse
from backend.app.models.etf_analysis import (
    PerformanceMetric,
)
from backend.app.models.etf_data_profile_api import (
    ETFDataProfileResponse,
)
from backend.app.models.performance_api import (
    ETFPerformanceItem,
    SupportedPerformancePeriod,
)


class ETFComparisonAPIBaseModel(BaseModel):
    """ETF 比較 API 共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
    )


class ETFComparisonDividendSummary(
    ETFComparisonAPIBaseModel
):
    """單一 ETF 配息歷史摘要。"""

    event_count: int = Field(
        ge=0,
    )

    latest_event_date: date | None = None

    latest_amount_per_unit: float | None = Field(
        default=None,
        ge=0,
    )

    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )


class ETFComparisonActual76WSummary(
    ETFComparisonAPIBaseModel
):
    """單一 ETF 正式 76W 摘要。"""

    record_count: int = Field(
        ge=0,
    )

    full_76w_count: int = Field(
        ge=0,
    )

    latest_ratio_pct: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    average_ratio_pct: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )


class ETFComparisonCompleteness(
    ETFComparisonAPIBaseModel
):
    """單一 ETF 比較資料完整度。"""

    available_section_count: int = Field(
        ge=0,
    )

    total_section_count: int = Field(
        ge=1,
    )

    score_pct: float = Field(
        ge=0,
        le=100,
    )

    available_sections: list[str]

    missing_sections: list[str]


class ETFComparisonItem(
    ETFComparisonAPIBaseModel
):
    """單一 ETF 的完整比較資料。"""

    etf: ETFResponse

    performance_items: list[
        ETFPerformanceItem
    ]

    dividend: ETFComparisonDividendSummary

    actual_76w: ETFComparisonActual76WSummary

    data_profile: ETFDataProfileResponse

    completeness: ETFComparisonCompleteness


class ETFComparisonResponse(
    ETFComparisonAPIBaseModel
):
    """2 至 4 檔 ETF 的比較回應。"""

    codes: list[str] = Field(
        min_length=2,
        max_length=4,
    )

    metric_code: PerformanceMetric

    periods: list[
        SupportedPerformancePeriod
    ] = Field(
        min_length=4,
        max_length=4,
    )

    items: list[
        ETFComparisonItem
    ] = Field(
        min_length=2,
        max_length=4,
    )
