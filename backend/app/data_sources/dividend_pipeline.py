"""TWSE ETF 配息正式匯入 Pipeline。"""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REJECTED_DATA_DIR,
)
from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.dividend_normalizer import (
    DividendNormalizationResult,
    normalize_twse_dividend_rows,
)
from backend.app.data_sources.dividend_quality_report import (
    DividendPipelineIssue,
    build_dividend_quality_report,
    save_dividend_artifacts,
    save_dividend_quality_report,
)
from backend.app.data_sources.twse_etf_dividend import (
    SOURCE_ID,
    extract_twse_dividend_rows,
    fetch_twse_dividend_html,
    save_twse_dividend_html_snapshot,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
)
from backend.app.repositories.dividend_repository import (
    DividendComponentUpsertSummary,
    DividendDatasetUpsertSummary,
    DividendUpsertSummary,
    upsert_dividend_dataset,
)
from backend.app.repositories.import_batch_repository import (
    ImportBatchCompletion,
    create_import_batch,
    mark_import_batch_failed,
    mark_import_batch_success,
)


PIPELINE_NAME = "dividend_pipeline"
ENDPOINT_ID = SOURCE_ID


@dataclass(
    frozen=True,
    slots=True,
)
class DividendPipelineResult:
    """配息 Pipeline 執行結果。"""

    batch_id: int
    raw_record_count: int
    accepted_dividend_count: int
    accepted_component_count: int
    rejected_record_count: int
    inserted_dividend_count: int
    updated_dividend_count: int
    inserted_component_count: int
    updated_component_count: int
    raw_snapshot_path: Path
    processed_path: Path
    rejected_path: Path
    quality_report_path: Path


def list_existing_etf_codes(
    database_path: str | Path,
    codes: set[str],
) -> set[str]:
    """取得資料庫中已存在的 ETF 代號。"""

    if not codes:
        return set()

    placeholders = ", ".join(
        "?"
        for _ in codes
    )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            SELECT code
            FROM etf_master
            WHERE code IN ({placeholders});
            """,
            sorted(codes),
        ).fetchall()

        return {
            row["code"]
            for row in rows
        }

    finally:
        connection.close()


def validate_twse_component_policy(
    result: DividendNormalizationResult,
) -> None:
    """防止預估資本利得被誤寫成實際 76W。"""

    invalid_actual = [
        record
        for record in result.components
        if (
            record.component_basis
            != DividendComponentBasis.ESTIMATED
        )
    ]

    if invalid_actual:
        raise ValueError(
            "TWSE 配息來源只能產生 ESTIMATED 組成"
        )

    if any(
        record.component_code == "76W"
        for record in result.components
    ):
        raise ValueError(
            "TWSE 預估配息來源不得產生 76W"
        )



def deduplicate_source_events(
    result: DividendNormalizationResult,
) -> tuple[
    DividendNormalizationResult,
    list[DividendPipelineIssue],
]:
    """合併重複事件，並拒絕互相矛盾的組成揭露。

    TWSE 頁面可能重複列出相同 ETF、相同除息日及
    相同配息金額，但附上不同的預估組成。事件本身
    可以保留一筆；互相矛盾的組成則全部拒絕，避免
    任意選擇其中一組比例。
    """

    unique_dividends = {}
    duplicate_event_keys: set[
        tuple[str, str]
    ] = set()
    conflicting_event_keys: set[
        tuple[str, str]
    ] = set()

    for record in result.dividends:
        event_key = (
            record.etf_code,
            record.source_event_id,
        )

        existing = unique_dividends.get(
            event_key
        )

        if existing is None:
            unique_dividends[event_key] = (
                record
            )
            continue

        duplicate_event_keys.add(
            event_key
        )

        existing_payload = (
            existing.model_dump(
                mode="json",
                exclude={
                    "import_batch_id",
                    "source_updated_at",
                },
            )
        )

        incoming_payload = (
            record.model_dump(
                mode="json",
                exclude={
                    "import_batch_id",
                    "source_updated_at",
                },
            )
        )

        if incoming_payload != existing_payload:
            conflicting_event_keys.add(
                event_key
            )

    unique_components = {}
    conflicting_component_keys: set[
        tuple[str, str]
    ] = set()

    for record in result.components:
        event_key = (
            record.etf_code,
            record.dividend_source_event_id,
        )

        component_key = (
            record.etf_code,
            record.dividend_source_event_id,
            record.component_basis.value,
            record.component_code,
            record.source_id,
        )

        existing = unique_components.get(
            component_key
        )

        if existing is None:
            unique_components[
                component_key
            ] = record
            continue

        existing_payload = (
            existing.model_dump(
                mode="json",
                exclude={
                    "import_batch_id",
                    "source_updated_at",
                },
            )
        )

        incoming_payload = (
            record.model_dump(
                mode="json",
                exclude={
                    "import_batch_id",
                    "source_updated_at",
                },
            )
        )

        if incoming_payload != existing_payload:
            conflicting_component_keys.add(
                event_key
            )

    accepted_dividends = [
        record
        for event_key, record
        in unique_dividends.items()
        if event_key not in conflicting_event_keys
    ]

    accepted_components = [
        record
        for component_key, record
        in unique_components.items()
        if (
            (
                component_key[0],
                component_key[1],
            )
            not in conflicting_event_keys
            and (
                component_key[0],
                component_key[1],
            )
            not in conflicting_component_keys
        )
    ]

    issues: list[
        DividendPipelineIssue
    ] = []

    for etf_code, source_event_id in sorted(
        conflicting_event_keys
    ):
        issues.append(
            DividendPipelineIssue(
                category=(
                    "duplicate_event_conflict"
                ),
                etf_code=etf_code,
                source_event_id=(
                    source_event_id
                ),
                reason=(
                    "相同來源事件具有互相矛盾的"
                    "配息事件欄位，整筆拒絕"
                ),
            )
        )

    for etf_code, source_event_id in sorted(
        conflicting_component_keys
        - conflicting_event_keys
    ):
        issues.append(
            DividendPipelineIssue(
                category=(
                    "conflicting_component_disclosure"
                ),
                etf_code=etf_code,
                source_event_id=(
                    source_event_id
                ),
                reason=(
                    "相同配息事件具有互相矛盾的"
                    "預估組成；保留事件但不匯入組成"
                ),
            )
        )

    collapsed_keys = (
        duplicate_event_keys
        - conflicting_event_keys
        - conflicting_component_keys
    )

    for etf_code, source_event_id in sorted(
        collapsed_keys
    ):
        issues.append(
            DividendPipelineIssue(
                category="duplicate_source_event",
                etf_code=etf_code,
                source_event_id=(
                    source_event_id
                ),
                reason=(
                    "官方來源重複列出相同配息事件，"
                    "已合併為一筆"
                ),
            )
        )

    return (
        DividendNormalizationResult(
            dividends=accepted_dividends,
            components=accepted_components,
            rejected=result.rejected,
        ),
        issues,
    )


def filter_known_etfs(
    result: DividendNormalizationResult,
    database_path: str | Path,
) -> tuple[
    DividendNormalizationResult,
    list[DividendPipelineIssue],
]:
    """排除尚未存在於 ETF 主資料的配息事件。"""

    existing_codes = list_existing_etf_codes(
        database_path=database_path,
        codes={
            record.etf_code
            for record in result.dividends
        },
    )

    accepted_dividends = [
        record
        for record in result.dividends
        if record.etf_code in existing_codes
    ]

    accepted_event_keys = {
        (
            record.etf_code,
            record.source_event_id,
        )
        for record in accepted_dividends
    }

    accepted_components = [
        record
        for record in result.components
        if (
            record.etf_code,
            record.dividend_source_event_id,
        )
        in accepted_event_keys
    ]

    issues = [
        DividendPipelineIssue(
            category="missing_etf_master",
            etf_code=record.etf_code,
            source_event_id=(
                record.source_event_id
            ),
            reason=(
                "找不到 ETF 主資料："
                f"{record.etf_code}"
            ),
        )
        for record in result.dividends
        if record.etf_code not in existing_codes
    ]

    return (
        DividendNormalizationResult(
            dividends=accepted_dividends,
            components=accepted_components,
            rejected=[],
        ),
        issues,
    )


def attach_import_batch(
    result: DividendNormalizationResult,
    batch_id: int,
) -> DividendNormalizationResult:
    """將匯入批次 ID 寫入事件與組成模型。"""

    return DividendNormalizationResult(
        dividends=[
            record.model_copy(
                update={
                    "import_batch_id": batch_id,
                }
            )
            for record in result.dividends
        ],
        components=[
            record.model_copy(
                update={
                    "import_batch_id": batch_id,
                }
            )
            for record in result.components
        ],
        rejected=[],
    )


def empty_import_summary(
) -> DividendDatasetUpsertSummary:
    """建立零筆資料的匯入摘要。"""

    return DividendDatasetUpsertSummary(
        dividends=DividendUpsertSummary(
            total_records=0,
            inserted_records=0,
            updated_records=0,
        ),
        components=(
            DividendComponentUpsertSummary(
                total_records=0,
                inserted_records=0,
                updated_records=0,
            )
        ),
    )


def run_dividend_pipeline(
    database_path: str | Path | None = None,
    raw_output_root: Path | None = None,
    processed_output_root: Path | None = None,
    rejected_output_root: Path | None = None,
    report_output_root: Path | None = None,
    html_text: str | None = None,
    run_at: datetime | None = None,
    etf_code: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    preserve_event_on_invalid_estimates: bool = False,
) -> DividendPipelineResult:
    """執行 TWSE ETF 配息完整匯入流程。"""

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

    raw_record_count = 0
    accepted_dividend_count = 0
    rejected_record_count = 0

    raw_snapshot_path: str | None = None
    processed_snapshot_path: str | None = None
    rejected_snapshot_path: str | None = None

    try:
        if html_text is None:
            html_text = (
                fetch_twse_dividend_html(
                    etf_code=etf_code,
                    start_year=start_year,
                    end_year=end_year,
                )
            )

        rows = extract_twse_dividend_rows(
            html_text
        )

        raw_record_count = len(rows)

        raw_snapshot = (
            save_twse_dividend_html_snapshot(
                html_text=html_text,
                output_root=(
                    raw_output_root
                    or (
                        RAW_DATA_DIR
                        / "dividends"
                    )
                ),
                downloaded_at=run_at,
            )
        )

        raw_snapshot_path = str(
            raw_snapshot.data_path
        )

        normalization_result = (
            normalize_twse_dividend_rows(
                rows,
                preserve_event_on_invalid_estimates=(
                    preserve_event_on_invalid_estimates
                ),
            )
        )

        (
            normalization_result,
            duplicate_issues,
        ) = deduplicate_source_events(
            normalization_result
        )

        issues = [
            DividendPipelineIssue(
                category="normalization",
                row_number=issue.row_number,
                etf_code=issue.etf_code,
                reason=issue.reason,
            )
            for issue in (
                normalization_result.rejected
            )
        ]

        issues.extend(
            duplicate_issues
        )

        known_result, missing_etf_issues = (
            filter_known_etfs(
                result=normalization_result,
                database_path=(
                    target_database_path
                ),
            )
        )

        issues.extend(
            missing_etf_issues
        )

        validate_twse_component_policy(
            known_result
        )

        import_result = attach_import_batch(
            result=known_result,
            batch_id=batch_id,
        )

        accepted_dividend_count = len(
            import_result.dividends
        )

        rejected_record_count = len(
            issues
        )

        artifacts = save_dividend_artifacts(
            batch_id=batch_id,
            source_id=SOURCE_ID,
            result=import_result,
            issues=issues,
            processed_root=(
                processed_output_root
                or (
                    PROCESSED_DATA_DIR
                    / "dividends"
                )
            ),
            rejected_root=(
                rejected_output_root
                or (
                    REJECTED_DATA_DIR
                    / "dividends"
                )
            ),
            created_at=run_at,
        )

        processed_snapshot_path = str(
            artifacts.processed_path
        )

        rejected_snapshot_path = str(
            artifacts.rejected_path
        )

        if import_result.dividends:
            import_summary = (
                upsert_dividend_dataset(
                    dividends=(
                        import_result.dividends
                    ),
                    components=(
                        import_result.components
                    ),
                    database_path=(
                        target_database_path
                    ),
                )
            )

        else:
            import_summary = (
                empty_import_summary()
            )

        report = build_dividend_quality_report(
            batch_id=batch_id,
            source_id=SOURCE_ID,
            raw_record_count=(
                raw_record_count
            ),
            raw_snapshot=raw_snapshot,
            result=import_result,
            issues=issues,
            import_summary=import_summary,
            artifact_paths=artifacts,
        )

        quality_report_path = (
            save_dividend_quality_report(
                batch_id=batch_id,
                source_id=SOURCE_ID,
                report=report,
                output_root=(
                    report_output_root
                ),
                created_at=run_at,
            )
        )

        inserted_record_count = (
            import_summary
            .dividends
            .inserted_records
            + import_summary
            .components
            .inserted_records
        )

        updated_record_count = (
            import_summary
            .dividends
            .updated_records
            + import_summary
            .components
            .updated_records
        )

        completion = ImportBatchCompletion(
            raw_record_count=(
                raw_record_count
            ),
            accepted_record_count=(
                accepted_dividend_count
            ),
            rejected_record_count=(
                rejected_record_count
            ),
            inserted_record_count=(
                inserted_record_count
            ),
            updated_record_count=(
                updated_record_count
            ),
            deleted_development_record_count=0,
            checksum_sha256=(
                raw_snapshot.checksum_sha256
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

        return DividendPipelineResult(
            batch_id=batch_id,
            raw_record_count=(
                raw_record_count
            ),
            accepted_dividend_count=(
                accepted_dividend_count
            ),
            accepted_component_count=len(
                import_result.components
            ),
            rejected_record_count=(
                rejected_record_count
            ),
            inserted_dividend_count=(
                import_summary
                .dividends
                .inserted_records
            ),
            updated_dividend_count=(
                import_summary
                .dividends
                .updated_records
            ),
            inserted_component_count=(
                import_summary
                .components
                .inserted_records
            ),
            updated_component_count=(
                import_summary
                .components
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
                raw_record_count
            ),
            accepted_record_count=(
                accepted_dividend_count
            ),
            rejected_record_count=(
                rejected_record_count
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


def build_argument_parser() -> argparse.ArgumentParser:
    """建立受控的目前／歷史配息查詢參數。"""

    parser = argparse.ArgumentParser(
        description="執行 TWSE ETF e添富配息 Pipeline"
    )
    parser.add_argument("--etf-code")
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument(
        "--preserve-event-on-invalid-estimates",
        action="store_true",
        help=(
            "保留日期與金額有效的父配息事件，"
            "但拒絕不完整或合計異常的預估組成"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """執行 TWSE ETF 配息 Pipeline。"""

    args = build_argument_parser().parse_args(argv)

    print("開始執行 TWSE ETF 配息 Pipeline")

    result = run_dividend_pipeline(
        etf_code=args.etf_code,
        start_year=args.start_year,
        end_year=args.end_year,
        preserve_event_on_invalid_estimates=(
            args.preserve_event_on_invalid_estimates
        ),
    )

    print("-" * 70)
    print("TWSE ETF 配息 Pipeline 執行成功")
    print(f"批次 ID：{result.batch_id}")
    print(
        f"原始事件："
        f"{result.raw_record_count}"
    )
    print(
        f"接受事件："
        f"{result.accepted_dividend_count}"
    )
    print(
        f"接受組成："
        f"{result.accepted_component_count}"
    )
    print(
        f"拒絕事件："
        f"{result.rejected_record_count}"
    )
    print(
        f"新增事件："
        f"{result.inserted_dividend_count}"
    )
    print(
        f"更新事件："
        f"{result.updated_dividend_count}"
    )
    print(
        f"新增組成："
        f"{result.inserted_component_count}"
    )
    print(
        f"更新組成："
        f"{result.updated_component_count}"
    )
    print(
        f"原始快照："
        f"{result.raw_snapshot_path}"
    )
    print(
        f"處理結果："
        f"{result.processed_path}"
    )
    print(
        f"拒絕資料："
        f"{result.rejected_path}"
    )
    print(
        f"品質報告："
        f"{result.quality_report_path}"
    )


if __name__ == "__main__":
    main()
