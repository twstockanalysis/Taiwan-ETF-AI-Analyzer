"""ETF 配息 Pipeline 產物與資料品質報告。"""

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
from backend.app.data_sources.dividend_normalizer import (
    DividendNormalizationResult,
)
from backend.app.data_sources.twse_etf_dividend import (
    RawHtmlSnapshot,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
    EstimatedDividendComponent,
)
from backend.app.repositories.dividend_repository import (
    DividendDatasetUpsertSummary,
)




def write_json(
    file_path: Path,
    payload: object,
) -> None:
    """將物件寫入 UTF-8 JSON。"""

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
    """建立檔名用 UTC 時間。"""

    if created_at is None:
        created_at = datetime.now(
            timezone.utc
        )

    return created_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )


@dataclass(
    frozen=True,
    slots=True,
)
class DividendPipelineIssue:
    """配息 Pipeline 拒絕資料。"""

    category: str
    etf_code: str
    reason: str
    row_number: int | None = None
    source_event_id: str | None = None


@dataclass(
    frozen=True,
    slots=True,
)
class DividendArtifactPaths:
    """配息 Processed 與 Rejected 產物位置。"""

    processed_path: Path
    rejected_path: Path


def save_dividend_artifacts(
    batch_id: int,
    source_id: str,
    result: DividendNormalizationResult,
    issues: list[DividendPipelineIssue],
    processed_root: Path | None = None,
    rejected_root: Path | None = None,
    created_at: datetime | None = None,
) -> DividendArtifactPaths:
    """保存配息事件、組成與拒絕資料。"""

    if processed_root is None:
        processed_root = (
            PROCESSED_DATA_DIR
            / "dividends"
        )

    if rejected_root is None:
        rejected_root = (
            REJECTED_DATA_DIR
            / "dividends"
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
        "dividends": [
            record.model_dump(
                mode="json"
            )
            for record in result.dividends
        ],
        "components": [
            record.model_dump(
                mode="json"
            )
            for record in result.components
        ],
    }

    rejected_payload = [
        {
            "category": issue.category,
            "row_number": issue.row_number,
            "etf_code": issue.etf_code,
            "source_event_id": (
                issue.source_event_id
            ),
            "reason": issue.reason,
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

    return DividendArtifactPaths(
        processed_path=processed_path,
        rejected_path=rejected_path,
    )


def build_dividend_quality_report(
    batch_id: int,
    source_id: str,
    raw_record_count: int,
    raw_snapshot: RawHtmlSnapshot,
    result: DividendNormalizationResult,
    issues: list[DividendPipelineIssue],
    import_summary: DividendDatasetUpsertSummary,
    artifact_paths: DividendArtifactPaths,
) -> dict[str, Any]:
    """建立配息匯入品質報告。"""

    accepted_dividend_count = len(
        result.dividends
    )

    accepted_component_count = len(
        result.components
    )

    rejected_record_count = len(
        issues
    )

    acceptance_rate = (
        accepted_dividend_count
        / raw_record_count
        if raw_record_count
        else 0.0
    )

    basis_counts = Counter(
        record.component_basis.value
        for record in result.components
    )

    component_code_counts = Counter(
        record.component_code
        for record in result.components
    )

    rejection_categories = Counter(
        issue.category
        for issue in issues
    )

    rejection_reasons = Counter(
        issue.reason
        for issue in issues
    )

    accepted_event_keys = {
        (
            record.etf_code,
            record.source_event_id,
        )
        for record in result.dividends
    }

    component_event_keys = {
        (
            record.etf_code,
            record.dividend_source_event_id,
        )
        for record in result.components
    }

    events_without_components = (
        accepted_event_keys
        - component_event_keys
    )

    warnings: list[str] = []

    if accepted_dividend_count == 0:
        warnings.append(
            "沒有任何配息事件可匯入"
        )

    if events_without_components:
        warnings.append(
            "部分配息事件沒有預估組成資料"
        )

    if basis_counts[
        DividendComponentBasis.ACTUAL.value
    ]:
        warnings.append(
            "TWSE 預估來源出現 ACTUAL 組成"
        )

    if component_code_counts["76W"]:
        warnings.append(
            "TWSE 預估來源出現 76W 代碼"
        )

    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "source_id": source_id,
        "status": "success",
        "raw_record_count": raw_record_count,
        "accepted_dividend_count": (
            accepted_dividend_count
        ),
        "accepted_component_count": (
            accepted_component_count
        ),
        "rejected_record_count": (
            rejected_record_count
        ),
        "acceptance_rate": round(
            acceptance_rate,
            6,
        ),
        "inserted_dividend_count": (
            import_summary
            .dividends
            .inserted_records
        ),
        "updated_dividend_count": (
            import_summary
            .dividends
            .updated_records
        ),
        "inserted_component_count": (
            import_summary
            .components
            .inserted_records
        ),
        "updated_component_count": (
            import_summary
            .components
            .updated_records
        ),
        "estimated_component_count": (
            basis_counts[
                DividendComponentBasis
                .ESTIMATED
                .value
            ]
        ),
        "actual_component_count": (
            basis_counts[
                DividendComponentBasis
                .ACTUAL
                .value
            ]
        ),
        "estimated_realized_gain_count": (
            component_code_counts[
                EstimatedDividendComponent
                .REALIZED_CAPITAL_GAIN
                .value
            ]
        ),
        "actual_76w_count": (
            component_code_counts["76W"]
        ),
        "events_without_components_count": (
            len(events_without_components)
        ),
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
            raw_snapshot.checksum_sha256
        ),
        "raw_snapshot_path": str(
            raw_snapshot.data_path
        ),
        "processed_snapshot_path": str(
            artifact_paths.processed_path
        ),
        "rejected_snapshot_path": str(
            artifact_paths.rejected_path
        ),
        "warnings": warnings,
        "notes": (
            "TWSE ETF e添富組成占比屬預估資料；"
            "EST_REALIZED_CAPITAL_GAIN 不等同 76W。"
        ),
    }


def save_dividend_quality_report(
    batch_id: int,
    source_id: str,
    report: dict[str, Any],
    output_root: Path | None = None,
    created_at: datetime | None = None,
) -> Path:
    """保存配息品質報告。"""

    if output_root is None:
        output_root = (
            PROCESSED_DATA_DIR
            / "reports"
            / "dividends"
        )

    if created_at is None:
        created_at = datetime.now(
            timezone.utc
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
