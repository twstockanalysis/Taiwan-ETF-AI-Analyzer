"""正式配息來源文件 Repository。"""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from backend.app.database.connection import (
    get_connection,
)
from backend.app.models.dividend_source_document import (
    SourceDocumentInformationBasis,
    SourceDocumentParseStatus,
)


@dataclass(
    frozen=True,
    slots=True,
)
class SourceDocumentRegistration:
    """來源文件版本登錄結果。"""

    document_id: int
    version_number: int
    is_new_version: bool


def normalize_required_text(
    value: str,
    field_name: str,
    *,
    lowercase: bool = False,
) -> str:
    """正規化必要文字欄位。"""

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} 不得為空白"
        )

    if lowercase:
        normalized = normalized.lower()

    return normalized


def register_dividend_source_document(
    *,
    source_id: str,
    source_document_id: str,
    source_url: str,
    downloaded_at: datetime,
    content_type: str,
    checksum_sha256: str,
    snapshot_path: str | Path,
    metadata_path: str | Path,
    database_path: str | Path | None = None,
) -> SourceDocumentRegistration:
    """登錄來源文件；相同內容不建立重複版本。"""

    normalized_source_id = (
        normalize_required_text(
            source_id,
            "source_id",
            lowercase=True,
        )
    )

    normalized_document_id = (
        normalize_required_text(
            source_document_id,
            "source_document_id",
        )
    )

    normalized_url = (
        normalize_required_text(
            source_url,
            "source_url",
        )
    )

    normalized_content_type = (
        normalize_required_text(
            content_type,
            "content_type",
            lowercase=True,
        )
    )

    normalized_checksum = (
        normalize_required_text(
            checksum_sha256,
            "checksum_sha256",
            lowercase=True,
        )
    )

    if len(normalized_checksum) != 64:
        raise ValueError(
            "checksum_sha256 必須是 64 字元"
        )

    if downloaded_at.tzinfo is None:
        raise ValueError(
            "downloaded_at 必須包含時區"
        )

    connection = get_connection(
        database_path
    )

    try:
        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        existing = connection.execute(
            """
            SELECT
                id,
                version_number
            FROM dividend_source_document
            WHERE source_id = ?
              AND source_document_id = ?
              AND checksum_sha256 = ?;
            """,
            (
                normalized_source_id,
                normalized_document_id,
                normalized_checksum,
            ),
        ).fetchone()

        if existing is not None:
            connection.commit()

            return SourceDocumentRegistration(
                document_id=int(
                    existing["id"]
                ),
                version_number=int(
                    existing["version_number"]
                ),
                is_new_version=False,
            )

        version_row = connection.execute(
            """
            SELECT
                COALESCE(
                    MAX(version_number),
                    0
                ) AS maximum_version
            FROM dividend_source_document
            WHERE source_id = ?
              AND source_document_id = ?;
            """,
            (
                normalized_source_id,
                normalized_document_id,
            ),
        ).fetchone()

        version_number = (
            int(version_row["maximum_version"])
            + 1
        )

        cursor = connection.execute(
            """
            INSERT INTO dividend_source_document (
                source_id,
                source_document_id,
                version_number,
                source_url,
                downloaded_at,
                content_type,
                information_basis,
                checksum_sha256,
                snapshot_path,
                metadata_path,
                parse_status
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            );
            """,
            (
                normalized_source_id,
                normalized_document_id,
                version_number,
                normalized_url,
                downloaded_at.isoformat(),
                normalized_content_type,
                (
                    SourceDocumentInformationBasis
                    .UNKNOWN
                    .value
                ),
                normalized_checksum,
                str(snapshot_path),
                str(metadata_path),
                (
                    SourceDocumentParseStatus
                    .DOWNLOADED
                    .value
                ),
            ),
        )

        if cursor.lastrowid is None:
            raise RuntimeError(
                "無法取得來源文件資料庫 ID"
            )

        connection.commit()

        return SourceDocumentRegistration(
            document_id=int(
                cursor.lastrowid
            ),
            version_number=version_number,
            is_new_version=True,
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_dividend_source_document_result(
    *,
    document_id: int,
    parse_status: SourceDocumentParseStatus,
    information_basis: (
        SourceDocumentInformationBasis
    ),
    database_path: str | Path | None = None,
    source_document_date: date | None = None,
    import_batch_id: int | None = None,
    parse_error: str | None = None,
) -> None:
    """更新來源文件解析與匯入結果。"""

    if document_id < 1:
        raise ValueError(
            "document_id 必須大於 0"
        )

    normalized_error = (
        parse_error.strip()
        if parse_error
        else None
    )

    connection = get_connection(
        database_path
    )

    try:
        cursor = connection.execute(
            """
            UPDATE dividend_source_document
            SET
                source_document_date = ?,
                information_basis = ?,
                parse_status = ?,
                parse_error = ?,
                import_batch_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (
                (
                    source_document_date
                    .isoformat()
                    if source_document_date
                    else None
                ),
                information_basis.value,
                parse_status.value,
                normalized_error,
                import_batch_id,
                document_id,
            ),
        )

        if cursor.rowcount != 1:
            raise KeyError(
                "找不到來源文件："
                f"{document_id}"
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_dividend_source_document(
    document_id: int,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """取得單一來源文件。"""

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            """
            SELECT *
            FROM dividend_source_document
            WHERE id = ?;
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def list_dividend_source_document_versions(
    source_id: str,
    source_document_id: str,
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """依版本新到舊列出同一官方文件。"""

    normalized_source_id = (
        normalize_required_text(
            source_id,
            "source_id",
            lowercase=True,
        )
    )

    normalized_document_id = (
        normalize_required_text(
            source_document_id,
            "source_document_id",
        )
    )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM dividend_source_document
            WHERE source_id = ?
              AND source_document_id = ?
            ORDER BY version_number DESC;
            """,
            (
                normalized_source_id,
                normalized_document_id,
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()
