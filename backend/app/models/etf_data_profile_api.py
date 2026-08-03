"""ETF 詳細頁資料來源與新鮮度 API 模型。"""

from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from backend.app.models.etf_analysis import (
    PerformanceMetric,
)
from backend.app.models.performance_api import (
    SupportedPerformancePeriod,
)


class ETFDataProfileBaseModel(
    BaseModel
):
    """ETF 資料概況 API 共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
    )


class ETFDataSourceReference(
    ETFDataProfileBaseModel
):
    """單一資料來源顯示資訊。"""

    source_id: str = Field(
        min_length=1,
    )

    display_name: str = Field(
        min_length=1,
    )


class ETFMasterDataProfile(
    ETFDataProfileBaseModel
):
    """ETF 主資料來源與資料集更新狀態。"""

    sources: list[
        ETFDataSourceReference
    ]

    latest_import_at: datetime | None = None


class ETFPerformanceDataProfile(
    ETFDataProfileBaseModel
):
    """ETF 市價績效來源與新鮮度。"""

    metric_code: PerformanceMetric

    sources: list[
        ETFDataSourceReference
    ]

    record_count: int = Field(
        ge=0,
    )

    available_periods: list[
        SupportedPerformancePeriod
    ]

    latest_as_of_date: date | None = None

    latest_import_at: datetime | None = None


class ETFDividendDataProfile(
    ETFDataProfileBaseModel
):
    """ETF 配息事件來源與新鮮度。"""

    sources: list[
        ETFDataSourceReference
    ]

    event_count: int = Field(
        ge=0,
    )

    latest_event_date: date | None = None

    latest_import_at: datetime | None = None


class ETFActualDividendDataProfile(
    ETFDataProfileBaseModel
):
    """ETF 正式配息組成來源與新鮮度。"""

    sources: list[
        ETFDataSourceReference
    ]

    actual_component_event_count: int = Field(
        ge=0,
    )

    actual_76w_event_count: int = Field(
        ge=0,
    )

    source_document_event_count: int = Field(
        ge=0,
    )

    latest_source_document_date: (
        date | None
    ) = None

    latest_import_at: datetime | None = None


class ETFDataProfileResponse(
    ETFDataProfileBaseModel
):
    """ETF 詳細頁資料來源與新鮮度回應。"""

    etf_code: str = Field(
        min_length=1,
        max_length=10,
    )

    master: ETFMasterDataProfile

    performance: ETFPerformanceDataProfile

    dividends: ETFDividendDataProfile

    actual_dividend: (
        ETFActualDividendDataProfile
    )
