"""正式配息資料品質 API 回應模型。"""

from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from backend.app.models.dividend_quality import (
    DividendReviewIssueType,
    DividendReviewStatus,
)


class DividendQualityAPIBaseModel(
    BaseModel
):
    """正式配息品質 API 共用設定。"""

    model_config = ConfigDict(
        extra="forbid",
    )


class ActualDividendCoverageResponse(
    DividendQualityAPIBaseModel
):
    """正式配息覆蓋率摘要。"""

    etf_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=10,
    )

    total_dividend_count: int = Field(
        ge=0,
    )

    estimated_component_event_count: int = (
        Field(
            ge=0,
        )
    )

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

    missing_actual_component_event_count: (
        int
    ) = Field(
        ge=0,
    )

    missing_source_document_event_count: (
        int
    ) = Field(
        ge=0,
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


class DividendReviewQueueItem(
    DividendQualityAPIBaseModel
):
    """單一正式配息待處理項目。"""

    queue_id: int = Field(
        ge=1,
    )

    dividend_id: int = Field(
        ge=1,
    )

    etf_code: str = Field(
        min_length=1,
        max_length=10,
    )

    source_event_id: str = Field(
        min_length=1,
    )

    ex_dividend_date: date | None = None

    amount_per_unit: float = Field(
        ge=0,
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    issue_type: DividendReviewIssueType

    suggested_source_id: str | None = None

    priority: int = Field(
        ge=1,
        le=100,
    )

    status: DividendReviewStatus

    notes: str | None = None

    resolution_document_id: int | None = (
        Field(
            default=None,
            ge=1,
        )
    )

    last_evaluated_at: datetime

    resolved_at: datetime | None = None

    created_at: datetime

    updated_at: datetime


class DividendReviewQueueResponse(
    DividendQualityAPIBaseModel
):
    """正式配息待處理佇列分頁回應。"""

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
        DividendReviewQueueItem
    ]
