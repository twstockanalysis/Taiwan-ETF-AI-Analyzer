"""正式配息覆蓋率與人工審核佇列模型。"""

from enum import StrEnum


class DividendReviewIssueType(StrEnum):
    """待處理正式配息資料缺失類型。"""

    MISSING_ACTUAL_COMPONENTS = (
        "MISSING_ACTUAL_COMPONENTS"
    )

    MISSING_SOURCE_DOCUMENT = (
        "MISSING_SOURCE_DOCUMENT"
    )


class DividendReviewStatus(StrEnum):
    """正式配息來源審核狀態。"""

    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    SKIPPED = "SKIPPED"
