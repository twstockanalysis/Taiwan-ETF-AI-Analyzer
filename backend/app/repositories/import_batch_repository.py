"""ETF 資料匯入批次 Repository。"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from backend.app.database.connection import get_connection


class ImportBatchStatus(StrEnum):
    """匯入批次狀態。"""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(
    frozen=True,
    slots=True,
)
class ImportBatchCompletion:
    """成功匯入批次的完整結果。"""

    raw_record_count: int
    accepted_record_count: int
    rejected_record_count: int
    inserted_record_count: int
    updated_record_count: int
    deleted_development_record_count: int
    checksum_sha256: str
    raw_snapshot_path: str
    processed_snapshot_path: str
    rejected_snapshot_path: str
    quality_report_path: str


def utc_now_text() -> str:
    """取得 UTC ISO 8601 時間。"""

    return datetime.now(
        timezone.utc
    ).isoformat()


def create_import_batch(
    pipeline_name: str,
    source_id: str,
    endpoint_id: str,
    database_path: str | Path | None = None,
    started_at: str | None = None,
) -> int:
    """建立執行中的匯入批次。

    Returns:
        int: 新批次 ID。
    """

    if started_at is None:
        started_at = utc_now_text()

    connection = get_connection(
        database_path
    )

    try:
        cursor = connection.execute(
            """
            INSERT INTO import_batch (
                pipeline_name,
                source_id,
                endpoint_id,
                started_at,
                status
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                pipeline_name,
                source_id,
                endpoint_id,
                started_at,
                ImportBatchStatus.RUNNING.value,
            ),
        )

        connection.commit()

        if cursor.lastrowid is None:
            raise RuntimeError(
                "無法取得匯入批次 ID"
            )

        return int(cursor.lastrowid)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def mark_import_batch_success(
    batch_id: int,
    completion: ImportBatchCompletion,
    database_path: str | Path | None = None,
    completed_at: str | None = None,
) -> None:
    """將匯入批次標記為成功。"""

    if completed_at is None:
        completed_at = utc_now_text()

    connection = get_connection(
        database_path
    )

    try:
        cursor = connection.execute(
            """
            UPDATE import_batch
            SET
                completed_at = ?,
                status = ?,
                raw_record_count = ?,
                accepted_record_count = ?,
                rejected_record_count = ?,
                inserted_record_count = ?,
                updated_record_count = ?,
                deleted_development_record_count = ?,
                checksum_sha256 = ?,
                raw_snapshot_path = ?,
                processed_snapshot_path = ?,
                rejected_snapshot_path = ?,
                quality_report_path = ?,
                error_message = NULL
            WHERE id = ?;
            """,
            (
                completed_at,
                ImportBatchStatus.SUCCESS.value,
                completion.raw_record_count,
                completion.accepted_record_count,
                completion.rejected_record_count,
                completion.inserted_record_count,
                completion.updated_record_count,
                completion.deleted_development_record_count,
                completion.checksum_sha256,
                completion.raw_snapshot_path,
                completion.processed_snapshot_path,
                completion.rejected_snapshot_path,
                completion.quality_report_path,
                batch_id,
            ),
        )

        if cursor.rowcount != 1:
            raise KeyError(
                f"找不到匯入批次：{batch_id}"
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def mark_import_batch_failed(
    batch_id: int,
    error_message: str,
    database_path: str | Path | None = None,
    raw_record_count: int = 0,
    accepted_record_count: int = 0,
    rejected_record_count: int = 0,
    raw_snapshot_path: str | None = None,
    processed_snapshot_path: str | None = None,
    rejected_snapshot_path: str | None = None,
    completed_at: str | None = None,
) -> None:
    """將匯入批次標記為失敗。"""

    if completed_at is None:
        completed_at = utc_now_text()

    connection = get_connection(
        database_path
    )

    try:
        cursor = connection.execute(
            """
            UPDATE import_batch
            SET
                completed_at = ?,
                status = ?,
                raw_record_count = ?,
                accepted_record_count = ?,
                rejected_record_count = ?,
                raw_snapshot_path = ?,
                processed_snapshot_path = ?,
                rejected_snapshot_path = ?,
                error_message = ?
            WHERE id = ?;
            """,
            (
                completed_at,
                ImportBatchStatus.FAILED.value,
                raw_record_count,
                accepted_record_count,
                rejected_record_count,
                raw_snapshot_path,
                processed_snapshot_path,
                rejected_snapshot_path,
                error_message,
                batch_id,
            ),
        )

        if cursor.rowcount != 1:
            raise KeyError(
                f"找不到匯入批次：{batch_id}"
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_import_batch(
    batch_id: int,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """取得指定匯入批次。"""

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            """
            SELECT *
            FROM import_batch
            WHERE id = ?;
            """,
            (batch_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def get_latest_import_batch(
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """取得最新匯入批次。"""

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            """
            SELECT *
            FROM import_batch
            ORDER BY id DESC
            LIMIT 1;
            """
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()