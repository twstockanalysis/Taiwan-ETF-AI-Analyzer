"""ETF 主資料完整更新 Pipeline。"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REJECTED_DATA_DIR,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.api_client import (
    fetch_json_records,
)
from backend.app.data_sources.endpoints import (
    get_api_endpoint,
)
from backend.app.data_sources.normalizers.twse_fund_master import (
    normalize_twse_fund_records,
)
from backend.app.data_sources.quality_report import (
    build_quality_report,
    save_normalization_artifacts,
    save_quality_report,
)
from backend.app.data_sources.raw_snapshot import (
    save_json_records_snapshot,
)
from backend.app.repositories.etf_import_repository import (
    upsert_etf_master,
)
from backend.app.repositories.import_batch_repository import (
    ImportBatchCompletion,
    create_import_batch,
    mark_import_batch_failed,
    mark_import_batch_success,
)


PIPELINE_NAME = "etf_master_pipeline"
ENDPOINT_ID = "twse_fund_master"


@dataclass(
    frozen=True,
    slots=True,
)
class ETFMasterPipelineResult:
    """ETF 主資料 Pipeline 結果。"""

    batch_id: int
    raw_record_count: int
    accepted_record_count: int
    rejected_record_count: int
    inserted_record_count: int
    updated_record_count: int
    quality_report_path: Path


def run_etf_master_pipeline(
    database_path: str | Path | None = None,
    raw_output_root: Path | None = None,
    processed_output_root: Path | None = None,
    rejected_output_root: Path | None = None,
    report_output_root: Path | None = None,
) -> ETFMasterPipelineResult:
    """執行 ETF 主資料完整更新流程。"""

    target_database_path = (
        initialize_database(
            database_path
        )
    )

    endpoint = get_api_endpoint(
        ENDPOINT_ID
    )

    started_at = datetime.now(
        timezone.utc
    )

    batch_id = create_import_batch(
        pipeline_name=PIPELINE_NAME,
        source_id=endpoint.source_id,
        endpoint_id=endpoint.endpoint_id,
        database_path=target_database_path,
        started_at=started_at.isoformat(),
    )

    raw_record_count = 0
    accepted_record_count = 0
    rejected_record_count = 0

    raw_snapshot_path: str | None = None
    processed_snapshot_path: str | None = None
    rejected_snapshot_path: str | None = None

    try:
        records = fetch_json_records(
            endpoint
        )

        raw_record_count = len(records)

        if raw_output_root is None:
            raw_output_root = (
                RAW_DATA_DIR
                / endpoint.dataset_kind.value
            )

        raw_snapshot = (
            save_json_records_snapshot(
                endpoint=endpoint,
                records=records,
                output_root=raw_output_root,
                downloaded_at=started_at,
            )
        )

        raw_snapshot_path = str(
            raw_snapshot.data_path
        )

        normalization_result = (
            normalize_twse_fund_records(
                records
            )
        )

        accepted_record_count = len(
            normalization_result.accepted
        )

        rejected_record_count = len(
            normalization_result.rejected
        )

        artifacts = (
            save_normalization_artifacts(
                batch_id=batch_id,
                endpoint_id=endpoint.endpoint_id,
                result=normalization_result,
                processed_root=(
                    processed_output_root
                    or (
                        PROCESSED_DATA_DIR
                        / "etf_master"
                    )
                ),
                rejected_root=(
                    rejected_output_root
                    or (
                        REJECTED_DATA_DIR
                        / "etf_master"
                    )
                ),
                created_at=started_at,
            )
        )

        processed_snapshot_path = str(
            artifacts.processed_path
        )

        rejected_snapshot_path = str(
            artifacts.rejected_path
        )

        if not normalization_result.accepted:
            raise ValueError(
                "正規化後沒有可匯入的 ETF"
            )

        import_summary = upsert_etf_master(
            records=normalization_result.accepted,
            database_path=target_database_path,
            remove_development_records=True,
        )

        quality_report = (
            build_quality_report(
                batch_id=batch_id,
                endpoint_id=endpoint.endpoint_id,
                raw_snapshot=raw_snapshot,
                result=normalization_result,
                import_summary=import_summary,
                artifact_paths=artifacts,
            )
        )

        quality_report_path = (
            save_quality_report(
                batch_id=batch_id,
                endpoint_id=endpoint.endpoint_id,
                report=quality_report,
                output_root=report_output_root,
                created_at=started_at,
            )
        )

        completion = ImportBatchCompletion(
            raw_record_count=(
                raw_record_count
            ),
            accepted_record_count=(
                accepted_record_count
            ),
            rejected_record_count=(
                rejected_record_count
            ),
            inserted_record_count=(
                import_summary.inserted_records
            ),
            updated_record_count=(
                import_summary.updated_records
            ),
            deleted_development_record_count=(
                import_summary
                .deleted_development_records
            ),
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
            database_path=target_database_path,
        )

        return ETFMasterPipelineResult(
            batch_id=batch_id,
            raw_record_count=(
                raw_record_count
            ),
            accepted_record_count=(
                accepted_record_count
            ),
            rejected_record_count=(
                rejected_record_count
            ),
            inserted_record_count=(
                import_summary.inserted_records
            ),
            updated_record_count=(
                import_summary.updated_records
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
            database_path=target_database_path,
            raw_record_count=(
                raw_record_count
            ),
            accepted_record_count=(
                accepted_record_count
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


def main() -> None:
    """執行 ETF 主資料 Pipeline。"""

    print("開始執行 ETF 主資料 Pipeline")

    result = run_etf_master_pipeline()

    print("-" * 70)
    print("ETF 主資料 Pipeline 執行成功")
    print(f"批次 ID：{result.batch_id}")
    print(
        f"原始筆數："
        f"{result.raw_record_count}"
    )
    print(
        f"接受筆數："
        f"{result.accepted_record_count}"
    )
    print(
        f"拒絕筆數："
        f"{result.rejected_record_count}"
    )
    print(
        f"新增筆數："
        f"{result.inserted_record_count}"
    )
    print(
        f"更新筆數："
        f"{result.updated_record_count}"
    )
    print(
        f"品質報告："
        f"{result.quality_report_path}"
    )


if __name__ == "__main__":
    main()