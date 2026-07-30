"""正式收益分配通知書 JSON 正規化。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
)

from backend.app.data_sources.actual_dividend_notice import (
    ActualDividendNoticeInput,
)


class ActualDividendDocumentEnvelope(
    BaseModel
):
    """正式配息 JSON 文件最外層格式。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    schema_version: Literal[1]

    notices: list[
        dict[str, Any]
    ] = Field(
        min_length=1,
    )


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendNormalizationIssue:
    """單筆正式通知書拒絕原因。"""

    notice_index: int
    etf_code: str
    source_document_id: str
    reason: str
    record: dict[str, Any]


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendNormalizationResult:
    """正式通知書正規化結果。"""

    accepted: list[
        ActualDividendNoticeInput
    ]

    rejected: list[
        ActualDividendNormalizationIssue
    ]

    raw_notice_count: int


def normalize_actual_dividend_payload(
    payload: object,
) -> ActualDividendNormalizationResult:
    """驗證文件外層並逐筆正規化通知書。"""

    envelope = (
        ActualDividendDocumentEnvelope
        .model_validate(payload)
    )

    accepted: list[
        ActualDividendNoticeInput
    ] = []

    rejected: list[
        ActualDividendNormalizationIssue
    ] = []

    for notice_index, record in enumerate(
        envelope.notices,
        start=1,
    ):
        try:
            notice = (
                ActualDividendNoticeInput
                .model_validate(record)
            )

        except ValidationError as error:
            rejected.append(
                ActualDividendNormalizationIssue(
                    notice_index=notice_index,
                    etf_code=str(
                        record.get(
                            "etf_code",
                            "",
                        )
                    ).strip().upper(),
                    source_document_id=str(
                        record.get(
                            "source_document_id",
                            "",
                        )
                    ).strip(),
                    reason=str(error),
                    record=record,
                )
            )

            continue

        accepted.append(
            notice
        )

    return ActualDividendNormalizationResult(
        accepted=accepted,
        rejected=rejected,
        raw_notice_count=len(
            envelope.notices
        ),
    )
