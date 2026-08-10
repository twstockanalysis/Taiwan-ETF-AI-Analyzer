"""M11-4 不可變候選分析決策紀錄 Repository。"""

import json
from pathlib import Path
from typing import Any

from backend.app.database.connection import get_connection


_JSON_FIELDS = (
    "request",
    "analysis",
    "rationale",
    "exclusions",
    "alternatives",
    "risk_notes",
)


def _decode_row(row) -> dict[str, Any]:
    result = dict(row)
    for field in _JSON_FIELDS:
        result[field] = json.loads(result.pop(f"{field}_json"))
    return result


def create_decision_record(
    *,
    candidate_etf_code: str,
    candidate_name: str,
    analysis_status: str,
    outcome: str,
    request: dict[str, Any],
    analysis: dict[str, Any],
    rationale: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    alternatives: list[dict[str, Any]],
    risk_notes: list[dict[str, Any]],
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """新增一筆快照；此 Repository 刻意不提供更新或刪除。"""

    values = {
        "request": request,
        "analysis": analysis,
        "rationale": rationale,
        "exclusions": exclusions,
        "alternatives": alternatives,
        "risk_notes": risk_notes,
    }
    encoded = {
        field: json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for field, value in values.items()
    }
    connection = get_connection(database_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO decision_record (
                record_type,
                candidate_etf_code,
                candidate_name,
                analysis_status,
                outcome,
                request_json,
                analysis_json,
                rationale_json,
                exclusions_json,
                alternatives_json,
                risk_notes_json
            )
            VALUES (
                'CANDIDATE_HOLDING_ANALYSIS',
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            );
            """,
            (
                candidate_etf_code,
                candidate_name,
                analysis_status,
                outcome,
                encoded["request"],
                encoded["analysis"],
                encoded["rationale"],
                encoded["exclusions"],
                encoded["alternatives"],
                encoded["risk_notes"],
            ),
        )
        record_id = int(cursor.lastrowid)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    result = get_decision_record(record_id, database_path)
    if result is None:
        raise RuntimeError("決策紀錄寫入後未能讀回")
    return result


def list_decision_records(
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    connection = get_connection(database_path)
    try:
        rows = connection.execute(
            """
            SELECT
                id,
                record_type,
                candidate_etf_code,
                candidate_name,
                analysis_status,
                outcome,
                created_at
            FROM decision_record
            ORDER BY created_at DESC, id DESC;
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_decision_record(
    record_id: int,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    connection = get_connection(database_path)
    try:
        row = connection.execute(
            """
            SELECT
                id,
                record_type,
                candidate_etf_code,
                candidate_name,
                analysis_status,
                outcome,
                request_json,
                analysis_json,
                rationale_json,
                exclusions_json,
                alternatives_json,
                risk_notes_json,
                created_at
            FROM decision_record
            WHERE id = ?;
            """,
            (record_id,),
        ).fetchone()
        return _decode_row(row) if row is not None else None
    finally:
        connection.close()
