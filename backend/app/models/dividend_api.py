"""ETF 配息查詢 API 資料模型。"""

from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from backend.app.models.etf_analysis import (
    DividendComponentBasis,
    DividendYieldBasis,
)


class DividendAPIBaseModel(BaseModel):
    """配息 API 回應模型共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
    )


class DividendEventItem(
    DividendAPIBaseModel
):
    """ETF 單次配息事件。"""

    dividend_id: int = Field(
        ge=1,
    )

    source_event_id: str = Field(
        min_length=1,
    )

    announcement_date: date | None = None

    ex_dividend_date: date | None = None

    record_date: date | None = None

    payment_date: date | None = None

    amount_per_unit: float = Field(
        ge=0,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    source_id: str = Field(
        min_length=1,
    )

    distribution_period: str | None = Field(
        default=None,
        pattern=r"^[0-9]{4}Q[1-4]$",
    )

    distribution_period_source_id: (
        str | None
    ) = Field(
        default=None,
        min_length=1,
    )

    yield_pct: float | None = Field(
        default=None,
        ge=0,
    )

    yield_basis: DividendYieldBasis | None = None

    yield_source_id: str | None = Field(
        default=None,
        min_length=1,
    )

    reference_trade_date: date | None = None

    reference_close_price: float | None = Field(
        default=None,
        gt=0,
    )


class ETFDividendHistoryResponse(
    DividendAPIBaseModel
):
    """ETF 配息歷史分頁回應。"""

    etf_code: str = Field(
        min_length=1,
        max_length=10,
    )

    total: int = Field(
        ge=0,
    )

    limit: int = Field(
        ge=1,
    )

    offset: int = Field(
        ge=0,
    )

    items: list[
        DividendEventItem
    ]


class DividendComponentItem(
    DividendAPIBaseModel
):
    """單筆配息組成。"""

    component_id: int = Field(
        ge=1,
    )

    dividend_id: int = Field(
        ge=1,
    )

    component_code: str = Field(
        min_length=1,
    )

    component_basis: DividendComponentBasis

    component_name: str | None = None

    amount_per_unit: float | None = Field(
        default=None,
        ge=0,
    )

    ratio_pct: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    source_id: str = Field(
        min_length=1,
    )


class DividendDetailResponse(
    DividendEventItem
):
    """單次配息事件及其全部組成。"""

    etf_code: str = Field(
        min_length=1,
        max_length=10,
    )

    components: list[
        DividendComponentItem
    ]

    selected_component_basis: (
        Literal[
            "ACTUAL",
            "ESTIMATED_FALLBACK",
        ]
        | None
    ) = None

    selected_components: list[
        DividendComponentItem
    ] = Field(
        default_factory=list,
    )


class DividendComponentListResponse(
    DividendAPIBaseModel
):
    """單次配息組成查詢回應。"""

    dividend_id: int = Field(
        ge=1,
    )

    total: int = Field(
        ge=0,
    )

    items: list[
        DividendComponentItem
    ]


class Actual76WHistoryItem(
    DividendAPIBaseModel
):
    """ETF 單次實際 76W 紀錄。"""

    dividend_id: int = Field(
        ge=1,
    )

    source_event_id: str = Field(
        min_length=1,
    )

    announcement_date: date | None = None

    ex_dividend_date: date | None = None

    record_date: date | None = None

    payment_date: date | None = None

    amount_per_unit: float = Field(
        ge=0,
        description="該次配息每單位金額",
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    component_amount_per_unit: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        description="76W 每單位金額",
    )

    ratio_pct: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    source_id: str = Field(
        min_length=1,
        description="實際 76W 資料來源",
    )


class Actual76WSummaryResponse(
    DividendAPIBaseModel
):
    """ETF 實際 76W 歷史摘要。"""

    etf_code: str = Field(
        min_length=1,
        max_length=10,
    )

    total_dividend_count: int = Field(
        ge=0,
    )

    actual_76w_record_count: int = Field(
        ge=0,
    )

    full_76w_count: int = Field(
        ge=0,
    )

    latest_76w_ratio_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    average_76w_ratio_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    analysis_record_count: int = Field(
        ge=0,
        description="綜合選擇器可用的資本利得事件數",
    )

    analysis_actual_count: int = Field(
        ge=0,
        description="採完整 ACTUAL 組成的分析事件數",
    )

    analysis_estimated_fallback_count: int = Field(
        ge=0,
        description="採完整 e添富組成替代的分析事件數",
    )

    full_realized_gain_count: int = Field(
        ge=0,
        description="資本利得比例為 100% 的分析事件數",
    )

    latest_realized_gain_ratio_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    average_realized_gain_ratio_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    latest_analysis_basis: (
        Literal["ACTUAL", "ESTIMATED_FALLBACK"] | None
    ) = None

    items: list[
        Actual76WHistoryItem
    ]
