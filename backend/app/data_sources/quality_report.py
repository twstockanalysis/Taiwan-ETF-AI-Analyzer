"""ETF 資料品質與正規化產物模組。"""

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
from backend.app.data_sources.normalizers.twse_fund_master import (
    NormalizationResult,
)
from backend.app.data_sources.raw_snapshot import (
    RawDataSnapshot,
)
from backend.app.repositories.etf_import_repository import (
    ETFImportSummary,
)


@dataclass(
    frozen=True,
    slots=True,
)
class NormalizationArtifactPaths:
    """正規化與拒絕資料檔案位置。"""

    processed_path: Path
    rejected_path: Path


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


def save_normalization_artifacts(
    batch_id: int,
    endpoint_id: str,
    result: NormalizationResult,
    processed_root: Path | None = None,
    rejected_root: Path | None = None,
    created_at: datetime | None = None,
) -> NormalizationArtifactPaths:
    """儲存正規化與拒絕資料。"""

    if processed_root is None:
        processed_root = (
            PROCESSED_DATA_DIR
            / "etf_master"
        )

    if rejected_root is None:
        rejected_root = (
            REJECTED_DATA_DIR
            / "etf_master"
        )

    timestamp = build_timestamp(
        created_at
    )

    processed_directory = (
        processed_root / endpoint_id
    )

    rejected_directory = (
        rejected_root / endpoint_id
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

    accepted_payload = [
        record.model_dump(
            mode="json"
        )
        for record in result.accepted
    ]

    rejected_payload = [
        {
            "index": item.index,
            "reason": item.reason,
            "record": item.record,
        }
        for item in result.rejected
    ]

    write_json(
        processed_path,
        accepted_payload,
    )

    write_json(
        processed_directory / "latest.json",
        accepted_payload,
    )

    write_json(
        rejected_path,
        rejected_payload,
    )

    write_json(
        rejected_directory / "latest.json",
        rejected_payload,
    )

    return NormalizationArtifactPaths(
        processed_path=processed_path,
        rejected_path=rejected_path,
    )


def build_quality_report(
    batch_id: int,
    endpoint_id: str,
    raw_snapshot: RawDataSnapshot,
    result: NormalizationResult,
    import_summary: ETFImportSummary,
    artifact_paths: NormalizationArtifactPaths,
) -> dict[str, Any]:
    """建立 ETF 資料品質摘要。"""

    accepted_count = len(
        result.accepted
    )

    rejected_count = len(
        result.rejected
    )

    total_count = (
        accepted_count
        + rejected_count
    )

    acceptance_rate = (
        accepted_count / total_count
        if total_count
        else 0.0
    )

    accepted_codes = [
        record.code
        for record in result.accepted
    ]

    duplicate_code_count = (
        len(accepted_codes)
        - len(set(accepted_codes))
    )

    missing_listing_date_count = sum(
        record.listing_date is None
        for record in result.accepted
    )

    active_count = sum(
        record.is_active
        for record in result.accepted
    )

    bond_count = sum(
        record.is_bond
        for record in result.accepted
    )

    rejection_reasons = Counter(
        item.reason
        for item in result.rejected
    )

    warnings: list[str] = []

    if accepted_count == 0:
        warnings.append(
            "沒有任何 ETF 通過正規化"
        )

    if duplicate_code_count:
        warnings.append(
            "正規化資料存在重複 ETF 代號"
        )

    if missing_listing_date_count:
        warnings.append(
            "部分 ETF 缺少上市日期"
        )

    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "endpoint_id": endpoint_id,
        "status": "success",
        "raw_record_count": (
            raw_snapshot.record_count
        ),
        "accepted_record_count": (
            accepted_count
        ),
        "rejected_record_count": (
            rejected_count
        ),
        "acceptance_rate": round(
            acceptance_rate,
            6,
        ),
        "active_etf_count": active_count,
        "bond_etf_count": bond_count,
        "missing_listing_date_count": (
            missing_listing_date_count
        ),
        "duplicate_code_count": (
            duplicate_code_count
        ),
        "inserted_record_count": (
            import_summary.inserted_records
        ),
        "updated_record_count": (
            import_summary.updated_records
        ),
        "deleted_development_record_count": (
            import_summary
            .deleted_development_records
        ),
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
    }


def save_quality_report(
    batch_id: int,
    endpoint_id: str,
    report: dict[str, Any],
    output_root: Path | None = None,
    created_at: datetime | None = None,
) -> Path:
    """儲存品質報告。"""

    if output_root is None:
        output_root = (
            PROCESSED_DATA_DIR
            / "reports"
            / "etf_master"
        )

    timestamp = build_timestamp(
        created_at
    )

    report_directory = (
        output_root / endpoint_id
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