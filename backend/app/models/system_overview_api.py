"""首頁系統資料總覽 API 回應模型。"""

from datetime import date, datetime
from typing import Literal

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


class SystemOverviewAPIBaseModel(
    BaseModel
):
    """系統總覽 API 共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
    )


class ETFOverview(
    SystemOverviewAPIBaseModel
):
    """ETF 主資料數量與更新時間。"""

    total_count: int = Field(
        ge=0,
    )

    active_count: int = Field(
        ge=0,
    )

    passive_count: int = Field(
        ge=0,
    )

    bond_count: int = Field(
        ge=0,
    )

    non_bond_count: int = Field(
        ge=0,
    )

    latest_master_import_at: (
        datetime | None
    ) = None


class PerformancePeriodCoverage(
    SystemOverviewAPIBaseModel
):
    """單一績效期間的 ETF 覆蓋狀態。"""

    period_code: (
        SupportedPerformancePeriod
    )

    etf_count: int = Field(
        ge=0,
    )

    coverage_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    latest_as_of_date: date | None = None


class PerformanceOverview(
    SystemOverviewAPIBaseModel
):
    """市價績效資料覆蓋與最新日期。"""

    metric_code: PerformanceMetric

    source_id: str = Field(
        min_length=1,
    )

    etf_count: int = Field(
        ge=0,
    )

    total_etf_count: int = Field(
        ge=0,
    )

    coverage_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    latest_as_of_date: date | None = None

    periods: list[
        PerformancePeriodCoverage
    ]


class DividendOverview(
    SystemOverviewAPIBaseModel
):
    """配息事件與正式資料覆蓋摘要。"""

    event_count: int = Field(
        ge=0,
    )

    etf_count: int = Field(
        ge=0,
    )

    latest_event_date: date | None = None

    actual_component_event_count: int = (
        Field(
            ge=0,
        )
    )

    actual_76w_event_count: int = Field(
        ge=0,
    )

    source_document_event_count: int = (
        Field(
            ge=0,
        )
    )

    actual_component_coverage_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    actual_76w_coverage_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    source_document_coverage_pct: (
        float | None
    ) = Field(
        default=None,
        ge=0,
        le=100,
    )

    latest_actual_source_document_date: (
        date | None
    ) = None


class ImportBatchOverviewItem(
    SystemOverviewAPIBaseModel
):
    """首頁顯示的最近匯入批次摘要。"""

    batch_id: int = Field(
        ge=1,
    )

    pipeline_name: str = Field(
        min_length=1,
    )

    source_id: str = Field(
        min_length=1,
    )

    endpoint_id: str = Field(
        min_length=1,
    )

    started_at: datetime

    completed_at: datetime | None = None

    status: Literal[
        "running",
        "success",
        "failed",
    ]

    raw_record_count: int = Field(
        ge=0,
    )

    accepted_record_count: int = Field(
        ge=0,
    )

    rejected_record_count: int = Field(
        ge=0,
    )

    inserted_record_count: int = Field(
        ge=0,
    )

    updated_record_count: int = Field(
        ge=0,
    )

    error_message: str | None = None


class SystemOverviewResponse(
    SystemOverviewAPIBaseModel
):
    """首頁系統總覽完整回應。"""

    api_status: Literal["healthy"]

    database_type: Literal["SQLite"]

    etfs: ETFOverview

    performance: PerformanceOverview

    dividends: DividendOverview

    recent_import_batches: list[
        ImportBatchOverviewItem
    ]
