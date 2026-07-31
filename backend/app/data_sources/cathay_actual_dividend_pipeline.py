"""國泰實際配息公告轉接 M8-4A Pipeline。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.actual_dividend_pipeline import (
    ActualDividendPipelineResult,
    run_actual_dividend_pipeline,
)
from backend.app.data_sources.actual_dividend_source_registry import (
    get_actual_dividend_source,
)
from backend.app.data_sources.cathay_actual_dividend_adapter import (
    SOURCE_ID,
    build_cathay_source_document_id,
    parse_cathay_actual_dividend_announcement,
)
from backend.app.data_sources.official_source_document import (
    capture_official_html_document,
)
from backend.app.models.dividend_source_document import (
    SourceDocumentInformationBasis,
    SourceDocumentParseStatus,
)
from backend.app.repositories.dividend_source_document_repository import (
    SourceDocumentRegistration,
    register_dividend_source_document,
    update_dividend_source_document_result,
)


@dataclass(
    frozen=True,
    slots=True,
)
class CathayActualDividendPipelineResult:
    """國泰公告來源匯入結果。"""

    source_document_database_id: int
    source_document_version: int
    source_document_is_new_version: bool
    source_snapshot_path: Path
    generated_input_path: Path
    actual_pipeline: (
        ActualDividendPipelineResult
    )


def save_generated_actual_input(
    *,
    notice,
    checksum_sha256: str,
    output_root: Path | None = None,
) -> Path:
    """保存 Adapter 產生的 M8-4A 標準 JSON。"""

    if output_root is None:
        output_root = (
            PROCESSED_DATA_DIR
            / "dividends"
            / "actual_source_inputs"
        )

    source_directory = (
        output_root / SOURCE_ID
    )

    source_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        source_directory
        / (
            f"{notice.source_document_id}_"
            f"{checksum_sha256}.json"
        )
    )

    payload = {
        "schema_version": 1,
        "notices": [
            notice.model_dump(
                mode="json"
            ),
        ],
    }

    file_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (
        source_directory / "latest.json"
    ).write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return file_path


def run_cathay_actual_dividend_pipeline(
    *,
    source_document_url: str,
    etf_code: str,
    database_path: str | Path | None = None,
    source_document_id: str | None = None,
    html_text: str | None = None,
    allow_network: bool = False,
    source_snapshot_root: Path | None = None,
    generated_input_root: Path | None = None,
    actual_raw_output_root: Path | None = None,
    actual_processed_output_root: Path | None = None,
    actual_rejected_output_root: Path | None = None,
    actual_report_output_root: Path | None = None,
    run_at: datetime | None = None,
) -> CathayActualDividendPipelineResult:
    """保存、解析並匯入國泰 ACTUAL 公告。"""

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

    source = get_actual_dividend_source(
        SOURCE_ID
    )

    resolved_document_id = (
        source_document_id.strip()
        if source_document_id
        else build_cathay_source_document_id(
            source_document_url
        )
    )

    snapshot = (
        capture_official_html_document(
            source=source,
            source_document_id=(
                resolved_document_id
            ),
            source_url=(
                source_document_url
            ),
            html_text=html_text,
            output_root=(
                source_snapshot_root
            ),
            downloaded_at=run_at,
            allow_network=allow_network,
        )
    )

    registration: (
        SourceDocumentRegistration
    ) = register_dividend_source_document(
        source_id=source.source_id,
        source_document_id=(
            resolved_document_id
        ),
        source_url=snapshot.source_url,
        downloaded_at=(
            snapshot.downloaded_at
        ),
        content_type=(
            snapshot.content_type
        ),
        checksum_sha256=(
            snapshot.checksum_sha256
        ),
        snapshot_path=(
            snapshot.data_path
        ),
        metadata_path=(
            snapshot.metadata_path
        ),
        database_path=(
            target_database_path
        ),
    )

    try:
        notice = (
            parse_cathay_actual_dividend_announcement(
                html_text=(
                    snapshot.data_path
                    .read_text(
                        encoding="utf-8"
                    )
                ),
                source_document_url=(
                    snapshot.source_url
                ),
                etf_code=etf_code,
                source_document_id=(
                    resolved_document_id
                ),
            )
        )

    except Exception as error:
        update_dividend_source_document_result(
            document_id=(
                registration.document_id
            ),
            parse_status=(
                SourceDocumentParseStatus
                .REJECTED
            ),
            information_basis=(
                SourceDocumentInformationBasis
                .UNKNOWN
            ),
            parse_error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
            database_path=(
                target_database_path
            ),
        )

        raise

    generated_input_path = (
        save_generated_actual_input(
            notice=notice,
            checksum_sha256=(
                snapshot.checksum_sha256
            ),
            output_root=(
                generated_input_root
            ),
        )
    )

    try:
        actual_result = (
            run_actual_dividend_pipeline(
                input_path=(
                    generated_input_path
                ),
                database_path=(
                    target_database_path
                ),
                raw_output_root=(
                    actual_raw_output_root
                ),
                processed_output_root=(
                    actual_processed_output_root
                ),
                rejected_output_root=(
                    actual_rejected_output_root
                ),
                report_output_root=(
                    actual_report_output_root
                ),
                run_at=run_at,
            )
        )

    except Exception as error:
        update_dividend_source_document_result(
            document_id=(
                registration.document_id
            ),
            parse_status=(
                SourceDocumentParseStatus
                .FAILED
            ),
            information_basis=(
                SourceDocumentInformationBasis
                .ACTUAL
            ),
            source_document_date=(
                notice.source_document_date
            ),
            parse_error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
            database_path=(
                target_database_path
            ),
        )

        raise

    update_dividend_source_document_result(
        document_id=(
            registration.document_id
        ),
        parse_status=(
            SourceDocumentParseStatus
            .PARSED
        ),
        information_basis=(
            SourceDocumentInformationBasis
            .ACTUAL
        ),
        source_document_date=(
            notice.source_document_date
        ),
        import_batch_id=(
            actual_result.batch_id
        ),
        database_path=(
            target_database_path
        ),
    )

    return CathayActualDividendPipelineResult(
        source_document_database_id=(
            registration.document_id
        ),
        source_document_version=(
            registration.version_number
        ),
        source_document_is_new_version=(
            registration.is_new_version
        ),
        source_snapshot_path=(
            snapshot.data_path
        ),
        generated_input_path=(
            generated_input_path
        ),
        actual_pipeline=actual_result,
    )


def build_argument_parser(
) -> argparse.ArgumentParser:
    """建立命令列參數。"""

    parser = argparse.ArgumentParser(
        description=(
            "解析國泰投信實際配息組成公告，"
            "並轉接 M8-4A Pipeline"
        )
    )

    parser.add_argument(
        "--url",
        required=True,
        help="國泰投信官方公告 HTTPS 網址",
    )

    parser.add_argument(
        "--etf-code",
        required=True,
        help="公告所屬 ETF 代號",
    )

    parser.add_argument(
        "--document-id",
        help=(
            "自訂穩定文件 ID；未提供時由"
            " /announcement/{id} 產生"
        ),
    )

    parser.add_argument(
        "--input-html",
        help=(
            "已人工下載的官方 HTML；"
            "提供時不進行網路下載"
        ),
    )

    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="明確允許程式下載官方公告",
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> None:
    """執行國泰公告 Adapter Pipeline。"""

    arguments = (
        build_argument_parser()
        .parse_args(argv)
    )

    html_text: str | None = None

    if arguments.input_html:
        input_path = Path(
            arguments.input_html
        )

        if not input_path.is_file():
            raise FileNotFoundError(
                "找不到官方 HTML 輸入檔："
                f"{input_path}"
            )

        html_text = input_path.read_text(
            encoding="utf-8-sig"
        )

    elif not arguments.allow_network:
        raise ValueError(
            "必須提供 --input-html，"
            "或明確指定 --allow-network"
        )

    result = (
        run_cathay_actual_dividend_pipeline(
            source_document_url=(
                arguments.url
            ),
            etf_code=(
                arguments.etf_code
            ),
            source_document_id=(
                arguments.document_id
            ),
            html_text=html_text,
            allow_network=(
                arguments.allow_network
            ),
        )
    )

    print(
        "國泰實際配息公告 Pipeline 執行成功"
    )

    print(
        "來源文件資料庫 ID："
        f"{result.source_document_database_id}"
    )

    print(
        "來源文件版本："
        f"{result.source_document_version}"
    )

    print(
        "是否新版本："
        f"{result.source_document_is_new_version}"
    )

    print(
        "正式配息批次 ID："
        f"{result.actual_pipeline.batch_id}"
    )

    print(
        "接受正式組成："
        f"{result.actual_pipeline.accepted_component_count}"
    )

    print(
        "來源快照："
        f"{result.source_snapshot_path}"
    )

    print(
        "標準輸入："
        f"{result.generated_input_path}"
    )


if __name__ == "__main__":
    main()
