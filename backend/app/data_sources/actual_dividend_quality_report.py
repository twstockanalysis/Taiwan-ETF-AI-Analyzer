"""正式收益分配通知書匯入產物與品質報告。"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
    REJECTED_DATA_DIR,
)
from backend.app.data_sources.actual_dividend_matcher import (
    MatchedActualDividendNotice,
)
from backend.app.models.etf_analysis import (
    ETFDividendComponentImportRecord,
)
from backend.app.repositories.dividend_repository import (
    DividendComponentUpsertSummary,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendPipelineIssue:
    """正式配息匯入拒絕資料。"""

    category: str
    etf_code: str
    source_document_id: str
    reason: str
    notice_index: int | None = None
    record: dict[str, Any] | None = None


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendArtifactPaths:
    """正式配息 Processed 與 Rejected 路徑。"""

    processed_path: Path
    rejected_path: Path


def write_json(
    file_path: Path,
    payload: object,
) -> None:
    """寫入 UTF-8 JSON。"""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def build_timestamp(
    created_at: datetime | None = None,
) -> str:
    """建立 UTC 檔名時間。"""

    if created_at is None:
        created_at = datetime.now(
            timezone.utc
        )

    return created_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )


def save_actual_dividend_artifacts(
    batch_id: int,
    source_id: str,
    matched: list[
        MatchedActualDividendNotice
    ],
    components: list[
        ETFDividendComponentImportRecord
    ],
    issues: list[
        ActualDividendPipelineIssue
    ],
    processed_root: Path | None = None,
    rejected_root: Path | None = None,
    created_at: datetime | None = None,
) -> ActualDividendArtifactPaths:
    """保存匹配結果、正式組成與拒絕資料。"""

    if processed_root is None:
        processed_root = (
            PROCESSED_DATA_DIR
            / "dividends"
            / "actual"
        )

    if rejected_root is None:
        rejected_root = (
            REJECTED_DATA_DIR
            / "dividends"
            / "actual"
        )

    timestamp = build_timestamp(
        created_at
    )

    processed_directory = (
        processed_root / source_id
    )

    rejected_directory = (
        rejected_root / source_id
    )

    file_name = (
        f"batch_{batch_id:06d}_"
        f"{timestamp}.json"
    )

    processed_path = (
        processed_directory / file_name
    )

    rejected_path = (
        rejected_directory / file_name
    )

    processed_payload = {
        "schema_version": 1,
        "source_id": source_id,
        "batch_id": batch_id,
        "matched_notices": [
            {
                "dividend_id": (
                    item.dividend_id
                ),
                "dividend_source_event_id": (
                    item
                    .dividend_source_event_id
                ),
                "notice": (
                    item.notice.model_dump(
                        mode="json"
                    )
                ),
            }
            for item in matched
        ],
        "components": [
            component.model_dump(
                mode="json"
            )
            for component in components
        ],
    }

    rejected_payload = [
        {
            "category": issue.category,
            "notice_index": (
                issue.notice_index
            ),
            "etf_code": issue.etf_code,
            "source_document_id": (
                issue.source_document_id
            ),
            "reason": issue.reason,
            "record": issue.record,
        }
        for issue in issues
    ]

    write_json(
        processed_path,
        processed_payload,
    )

    write_json(
        processed_directory / "latest.json",
        processed_payload,
    )

    write_json(
        rejected_path,
        rejected_payload,
    )

    write_json(
        rejected_directory / "latest.json",
        rejected_payload,
    )

    return ActualDividendArtifactPaths(
        processed_path=processed_path,
        rejected_path=rejected_path,
    )


def build_actual_dividend_quality_report(
    batch_id: int,
    source_id: str,
    raw_notice_count: int,
    matched: list[
        MatchedActualDividendNotice
    ],
    components: list[
        ETFDividendComponentImportRecord
    ],
    issues: list[
        ActualDividendPipelineIssue
    ],
    import_summary: (
        DividendComponentUpsertSummary
    ),
    checksum_sha256: str,
    raw_snapshot_path: Path,
    artifact_paths: (
        ActualDividendArtifactPaths
    ),
) -> dict[str, Any]:
    """建立正式配息匯入品質摘要。"""

    component_code_counts = Counter(
        component.component_code
        for component in components
    )

    rejection_categories = Counter(
        issue.category
        for issue in issues
    )

    rejection_reasons = Counter(
        issue.reason
        for issue in issues
    )

    warnings: list[str] = []

    if not matched:
        warnings.append(
            "沒有正式通知書成功匹配配息事件"
        )

    if components and not (
        component_code_counts["76W"]
    ):
        warnings.append(
            "本批正式通知書沒有 76W 組成"
        )

    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "source_id": source_id,
        "status": "success",
        "raw_notice_count": (
            raw_notice_count
        ),
        "accepted_notice_count": len(
            matched
        ),
        "accepted_component_count": len(
            components
        ),
        "rejected_notice_count": len(
            issues
        ),
        "inserted_component_count": (
            import_summary.inserted_records
        ),
        "updated_component_count": (
            import_summary.updated_records
        ),
        "actual_76w_count": (
            component_code_counts["76W"]
        ),
        "component_code_counts": [
            {
                "component_code": code,
                "count": count,
            }
            for code, count
            in component_code_counts.most_common()
        ],
        "rejection_categories": [
            {
                "category": category,
                "count": count,
            }
            for category, count
            in rejection_categories.most_common()
        ],
        "top_rejection_reasons": [
            {
                "reason": reason,
                "count": count,
            }
            for reason, count
            in rejection_reasons.most_common(10)
        ],
        "checksum_sha256": (
            checksum_sha256
        ),
        "raw_snapshot_path": str(
            raw_snapshot_path
        ),
        "processed_snapshot_path": str(
            artifact_paths.processed_path
        ),
        "rejected_snapshot_path": str(
            artifact_paths.rejected_path
        ),
        "warnings": warnings,
        "notes": (
            "本 Pipeline 只匯入來源明確標示為"
            " ACTUAL 的正式所得代碼；"
            "EST_REALIZED_CAPITAL_GAIN 不會轉成 76W。"
        ),
    }


def save_actual_dividend_quality_report(
    batch_id: int,
    source_id: str,
    report: dict[str, Any],
    output_root: Path | None = None,
    created_at: datetime | None = None,
) -> Path:
    """保存正式配息品質報告。"""

    if output_root is None:
        output_root = (
            PROCESSED_DATA_DIR
            / "reports"
            / "dividends"
            / "actual"
        )

    timestamp = build_timestamp(
        created_at
    )

    report_directory = (
        output_root / source_id
    )

    report_path = (
        report_directory
        / (
            f"batch_{batch_id:06d}_"
            f"{timestamp}.report.json"
        )
    )

    write_json(
        report_path,
        report,
    )

    write_json(
        report_directory / "latest.json",
        report,
    )

    return report_path
