"""正式配息來源文件狀態模型。"""

from enum import StrEnum


class SourceDocumentInformationBasis(
    StrEnum
):
    """來源文件揭露的資訊性質。"""

    UNKNOWN = "UNKNOWN"
    ACTUAL = "ACTUAL"
    ESTIMATED = "ESTIMATED"


class SourceDocumentParseStatus(
    StrEnum
):
    """來源文件處理狀態。"""

    DOWNLOADED = "downloaded"
    PARSED = "parsed"
    REJECTED = "rejected"
    FAILED = "failed"
