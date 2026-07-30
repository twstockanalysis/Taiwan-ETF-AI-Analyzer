"""正式收益分配通知書 JSON 匯入 Pipeline。"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REJECTED_DATA_DIR,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.actual_dividend_matcher import (
    match_actual_dividend_notices,
)
from backend.app.data_sources.actual_dividend_normalizer import (
    normalize_actual_dividend_payload,
)
from backend.app.data_sources.actual_dividend_quality_report import (
    ActualDividendPipelineIssue,
    build_actual_dividend_quality_report,
    save_actual_dividend_artifacts,
    save_actual_dividend_quality_report,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
    ETFDividendComponentImportRecord,
)
from backend.app.repositories.dividend_repository import (
    DividendComponentUpsertSummary,
    upsert_dividend_component_records,
)
from backend.app.repositories.import_batch_repository import (
    ImportBatchCompletion,
    create_import_batch,
    mark_import_batch_failed,
    mark_import_batch_success,
)


PIPELINE_NAME = "actual_dividend_pipeline"
SOURCE_ID = "actual_dividend_notice"
ENDPOINT_ID = "actual_dividend_json_import"


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendRawSnapshot:
    """正式通知書原始 JSON 快照。"""

    data_path: Path
    metadata_path: Path
    checksum_sha256: str


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendPipelineResult:
    """正式配息匯入結果。"""

    batch_id: int
    raw_notice_count: int
    accepted_notice_count: int
    accepted_component_count: int
    rejected_notice_count: int
    inserted_component_count: int
    updated_component_count: int
    raw_snapshot_path: Path
    processed_path: Path
    rejected_path: Path
    quality_report_path: Path


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


def save_actual_dividend_raw_snapshot(
    input_path: Path,
    output_root: Path | None = None,
    downloaded_at: datetime | None = None,
) -> ActualDividendRawSnapshot:
    """保存人工確認過的正式通知書 JSON。"""

    if downloaded_at is None:
        downloaded_at = datetime.now(
            timezone.utc
        )

    if output_root is None:
        output_root = (
            RAW_DATA_DIR
            / "dividends"
            / "actual"
        )

    source_directory = (
        output_root / SOURCE_ID
    )

    source_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_bytes = input_path.read_bytes()

    checksum = hashlib.sha256(
        raw_bytes
    ).hexdigest()

    timestamp = downloaded_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    data_path = (
        source_directory
        / (
            f"{SOURCE_ID}_"
            f"{timestamp}.json"
        )
    )

    metadata_path = (
        source_directory
        / (
            f"{SOURCE_ID}_"
            f"{timestamp}.meta.json"
        )
    )

    data_path.write_bytes(
        raw_bytes
    )

    metadata = {
        "schema_version": 1,
        "source_id": SOURCE_ID,
        "input_path": str(
            input_path.resolve()
        ),
        "captured_at": (
            downloaded_at.isoformat()
        ),
        "checksum_sha256": checksum,
        "data_path": str(data_path),
    }

    write_json(
        metadata_path,
        metadata,
    )

    (
        source_directory / "latest.json"
    ).write_bytes(
        raw_bytes
    )

    write_json(
        source_directory
        / "latest.meta.json",
        metadata,
    )

    return ActualDividendRawSnapshot(
        data_path=data_path,
        metadata_path=metadata_path,
        checksum_sha256=checksum,
    )


def load_json_payload(
    input_path: Path,
) -> object:
    """讀取正式通知書 JSON。"""

    return json.loads(
        input_path.read_text(
            encoding="utf-8-sig"
        )
    )


def build_actual_components(
    matched_notices,
    batch_id: int,
) -> list[
    ETFDividendComponentImportRecord
]:
    """將唯一匹配通知書轉成 ACTUAL 組成。"""

    components: list[
        ETFDividendComponentImportRecord
    ] = []

    for matched in matched_notices:
        for component in (
            matched.notice.components
        ):
            components.append(
                ETFDividendComponentImportRecord(
                    etf_code=(
                        matched.notice.etf_code
                    ),
                    dividend_source_event_id=(
                        matched
                        .dividend_source_event_id
                    ),
                    component_code=(
                        component.component_code
                    ),
                    component_basis=(
                        DividendComponentBasis
                        .ACTUAL
                    ),
                    component_name=(
                        component.component_name
                    ),
                    amount_per_unit=(
                        component.amount_per_unit
                    ),
                    ratio_pct=(
                        component.ratio_pct
                    ),
                    source_id=(
                        matched.notice.source_id
                    ),
                    import_batch_id=batch_id,
                )
            )

    return components


def empty_component_summary(
) -> DividendComponentUpsertSummary:
    """建立零筆正式組成匯入摘要。"""

    return DividendComponentUpsertSummary(
        total_records=0,
        inserted_records=0,
        updated_records=0,
    )


def build_pipeline_issues(
    normalization_result,
    match_result,
) -> list[
    ActualDividendPipelineIssue
]:
    """整合正規化與事件匹配問題。"""

    issues = [
        ActualDividendPipelineIssue(
            category="normalization",
            notice_index=(
                issue.notice_index
            ),
            etf_code=issue.etf_code,
            source_document_id=(
                issue.source_document_id
            ),
            reason=issue.reason,
            record=issue.record,
        )
        for issue in (
            normalization_result.rejected
        )
    ]

    issues.extend(
        ActualDividendPipelineIssue(
            category=issue.category,
            etf_code=issue.etf_code,
            source_document_id=(
                issue.source_document_id
            ),
            reason=issue.reason,
        )
        for issue in match_result.rejected
    )

    return issues


def run_actual_dividend_pipeline(
    input_path: str | Path,
    database_path: str | Path | None = None,
    raw_output_root: Path | None = None,
    processed_output_root: Path | None = None,
    rejected_output_root: Path | None = None,
    report_output_root: Path | None = None,
    run_at: datetime | None = None,
) -> ActualDividendPipelineResult:
    """匯入人工確認過的正式收益分配通知書。"""

    resolved_input_path = Path(
        input_path
    )

    if not resolved_input_path.is_file():
        raise FileNotFoundError(
            "找不到正式配息輸入檔："
            f"{resolved_input_path}"
        )

    target_database_path = (
        initialize_database(
            database_path
        )
    )

    if run_at is None:
        run_at = datetime.now(
            timezone.utc
        )

    if run_at.tzinfo is None:
        raise ValueError(
            "run_at 必須包含時區"
        )

    batch_id = create_import_batch(
        pipeline_name=PIPELINE_NAME,
        source_id=SOURCE_ID,
        endpoint_id=ENDPOINT_ID,
        database_path=target_database_path,
        started_at=run_at.isoformat(),
    )

    raw_notice_count = 0
    accepted_notice_count = 0
    rejected_notice_count = 0

    raw_snapshot_path: str | None = None
    processed_snapshot_path: str | None = None
    rejected_snapshot_path: str | None = None

    try:
        raw_snapshot = (
            save_actual_dividend_raw_snapshot(
                input_path=resolved_input_path,
                output_root=(
                    raw_output_root
                    or (
                        RAW_DATA_DIR
                        / "dividends"
                        / "actual"
                    )
                ),
                downloaded_at=run_at,
            )
        )

        raw_snapshot_path = str(
            raw_snapshot.data_path
        )

        payload = load_json_payload(
            resolved_input_path
        )

        normalization_result = (
            normalize_actual_dividend_payload(
                payload
            )
        )

        raw_notice_count = (
            normalization_result
            .raw_notice_count
        )

        match_result = (
            match_actual_dividend_notices(
                notices=(
                    normalization_result
                    .accepted
                ),
                database_path=(
                    target_database_path
                ),
            )
        )

        issues = build_pipeline_issues(
            normalization_result,
            match_result,
        )

        components = build_actual_components(
            matched_notices=(
                match_result.matched
            ),
            batch_id=batch_id,
        )

        accepted_notice_count = len(
            match_result.matched
        )

        rejected_notice_count = len(
            issues
        )

        artifacts = (
            save_actual_dividend_artifacts(
                batch_id=batch_id,
                source_id=SOURCE_ID,
                matched=(
                    match_result.matched
                ),
                components=components,
                issues=issues,
                processed_root=(
                    processed_output_root
                    or (
                        PROCESSED_DATA_DIR
                        / "dividends"
                        / "actual"
                    )
                ),
                rejected_root=(
                    rejected_output_root
                    or (
                        REJECTED_DATA_DIR
                        / "dividends"
                        / "actual"
                    )
                ),
                created_at=run_at,
            )
        )

        processed_snapshot_path = str(
            artifacts.processed_path
        )

        rejected_snapshot_path = str(
            artifacts.rejected_path
        )

        if components:
            import_summary = (
                upsert_dividend_component_records(
                    records=components,
                    database_path=(
                        target_database_path
                    ),
                )
            )

        else:
            import_summary = (
                empty_component_summary()
            )

        report = (
            build_actual_dividend_quality_report(
                batch_id=batch_id,
                source_id=SOURCE_ID,
                raw_notice_count=(
                    raw_notice_count
                ),
                matched=(
                    match_result.matched
                ),
                components=components,
                issues=issues,
                import_summary=(
                    import_summary
                ),
                checksum_sha256=(
                    raw_snapshot
                    .checksum_sha256
                ),
                raw_snapshot_path=(
                    raw_snapshot.data_path
                ),
                artifact_paths=artifacts,
            )
        )

        quality_report_path = (
            save_actual_dividend_quality_report(
                batch_id=batch_id,
                source_id=SOURCE_ID,
                report=report,
                output_root=(
                    report_output_root
                    or (
                        PROCESSED_DATA_DIR
                        / "reports"
                        / "dividends"
                        / "actual"
                    )
                ),
                created_at=run_at,
            )
        )

        completion = ImportBatchCompletion(
            raw_record_count=(
                raw_notice_count
            ),
            accepted_record_count=(
                accepted_notice_count
            ),
            rejected_record_count=(
                rejected_notice_count
            ),
            inserted_record_count=(
                import_summary
                .inserted_records
            ),
            updated_record_count=(
                import_summary
                .updated_records
            ),
            deleted_development_record_count=0,
            checksum_sha256=(
                raw_snapshot
                .checksum_sha256
            ),
            raw_snapshot_path=(
                raw_snapshot_path
            ),
            processed_snapshot_path=(
                processed_snapshot_path
            ),
            rejected_snapshot_path=(
                rejected_snapshot_path
            ),
            quality_report_path=str(
                quality_report_path
            ),
        )

        mark_import_batch_success(
            batch_id=batch_id,
            completion=completion,
            database_path=(
                target_database_path
            ),
        )

        return ActualDividendPipelineResult(
            batch_id=batch_id,
            raw_notice_count=(
                raw_notice_count
            ),
            accepted_notice_count=(
                accepted_notice_count
            ),
            accepted_component_count=len(
                components
            ),
            rejected_notice_count=(
                rejected_notice_count
            ),
            inserted_component_count=(
                import_summary
                .inserted_records
            ),
            updated_component_count=(
                import_summary
                .updated_records
            ),
            raw_snapshot_path=(
                raw_snapshot.data_path
            ),
            processed_path=(
                artifacts.processed_path
            ),
            rejected_path=(
                artifacts.rejected_path
            ),
            quality_report_path=(
                quality_report_path
            ),
        )

    except Exception as error:
        mark_import_batch_failed(
            batch_id=batch_id,
            error_message=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
            database_path=(
                target_database_path
            ),
            raw_record_count=(
                raw_notice_count
            ),
            accepted_record_count=(
                accepted_notice_count
            ),
            rejected_record_count=(
                rejected_notice_count
            ),
            raw_snapshot_path=(
                raw_snapshot_path
            ),
            processed_snapshot_path=(
                processed_snapshot_path
            ),
            rejected_snapshot_path=(
                rejected_snapshot_path
            ),
        )

        raise


def build_argument_parser(
) -> argparse.ArgumentParser:
    """建立命令列參數。"""

    parser = argparse.ArgumentParser(
        description=(
            "匯入人工確認過的正式"
            " ETF 收益分配通知書 JSON"
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="正式配息 JSON 檔案路徑",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> None:
    """執行正式配息 JSON Pipeline。"""

    arguments = (
        build_argument_parser()
        .parse_args(argv)
    )

    print(
        "開始執行正式收益分配通知書 Pipeline"
    )

    result = run_actual_dividend_pipeline(
        input_path=arguments.input
    )

    print("-" * 70)
    print("正式配息 Pipeline 執行成功")
    print(f"批次 ID：{result.batch_id}")
    print(
        "原始通知書："
        f"{result.raw_notice_count}"
    )
    print(
        "接受通知書："
        f"{result.accepted_notice_count}"
    )
    print(
        "接受組成："
        f"{result.accepted_component_count}"
    )
    print(
        "拒絕通知書："
        f"{result.rejected_notice_count}"
    )
    print(
        "新增組成："
        f"{result.inserted_component_count}"
    )
    print(
        "更新組成："
        f"{result.updated_component_count}"
    )
    print(
        "原始快照："
        f"{result.raw_snapshot_path}"
    )
    print(
        "處理結果："
        f"{result.processed_path}"
    )
    print(
        "拒絕資料："
        f"{result.rejected_path}"
    )
    print(
        "品質報告："
        f"{result.quality_report_path}"
    )


if __name__ == "__main__":
    main()
