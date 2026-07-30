"""ETF 績效查詢 API 資料模型。"""

from datetime import date
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from backend.app.models.etf_analysis import (
    PerformanceMetric,
    PerformancePeriod,
)


class SupportedPerformancePeriod(StrEnum):
    """目前 API 支援的 ETF 績效期間。"""

    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"

    def to_performance_period(
        self,
    ) -> PerformancePeriod:
        """轉換成核心績效期間列舉。"""

        return PerformancePeriod(
            self.value
        )


class PerformanceAPIBaseModel(BaseModel):
    """績效 API 回應模型共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
    )


class PerformanceRankingItem(
    PerformanceAPIBaseModel
):
    """績效排行榜單筆資料。"""

    rank: int = Field(
        ge=1,
        description="排行榜名次",
    )

    etf_code: str = Field(
        min_length=1,
        max_length=10,
        description="ETF 證券代號",
    )

    name: str = Field(
        min_length=1,
        description="ETF 名稱",
    )

    is_active: bool = Field(
        description="是否為主動式 ETF",
    )

    is_bond: bool = Field(
        description="是否為債券 ETF",
    )

    as_of_date: date = Field(
        description="績效資料基準日",
    )

    period_code: PerformancePeriod = Field(
        description="績效期間",
    )

    metric_code: PerformanceMetric = Field(
        description="績效計算類型",
    )

    return_pct: float = Field(
        ge=-100,
        description="期間報酬率百分比",
    )

    source_id: str = Field(
        min_length=1,
        description="資料來源識別碼",
    )


class PerformanceRankingResponse(
    PerformanceAPIBaseModel
):
    """績效排行榜分頁回應。"""

    period_code: PerformancePeriod

    metric_code: PerformanceMetric

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
        PerformanceRankingItem
    ]


class ETFPerformanceItem(
    PerformanceAPIBaseModel
):
    """單一 ETF 的單一期間最新績效。"""

    as_of_date: date

    period_code: PerformancePeriod

    metric_code: PerformanceMetric

    return_pct: float = Field(
        ge=-100,
    )

    source_id: str = Field(
        min_length=1,
    )


class ETFPerformanceResponse(
    PerformanceAPIBaseModel
):
    """單一 ETF 多期間績效回應。"""

    etf_code: str = Field(
        min_length=1,
        max_length=10,
    )

    metric_code: PerformanceMetric

    items: list[
        ETFPerformanceItem
    ]
