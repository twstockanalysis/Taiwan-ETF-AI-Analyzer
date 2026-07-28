"""ETF 主資料 Repository。"""

import sqlite3
from pathlib import Path
from typing import Any

from backend.app.database.connection import get_connection


ETF_SELECT_COLUMNS = """
    code,
    name,
    is_active,
    is_bond,
    listing_date,
    fund_size,
    expense_ratio
"""


def row_to_dictionary(
    row: sqlite3.Row,
) -> dict[str, Any]:
    """將 SQLite Row 轉換成一般字典。

    Args:
        row: SQLite 查詢結果。

    Returns:
        dict[str, Any]: 可交由 API 處理的字典。
    """

    return {
        key: row[key]
        for key in row.keys()
    }


def list_etfs(
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """取得所有 ETF 主資料。

    Args:
        database_path:
            指定資料庫路徑。
            未提供時使用預設開發資料庫。

    Returns:
        list[dict[str, Any]]: ETF 資料列表。
    """

    connection = get_connection(database_path)

    try:
        rows = connection.execute(
            f"""
            SELECT
                {ETF_SELECT_COLUMNS}
            FROM etf_master
            ORDER BY code;
            """
        ).fetchall()

        return [
            row_to_dictionary(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_etf_by_code(
    code: str,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """依 ETF 代號取得單筆主資料。

    Args:
        code: ETF 證券代號。
        database_path:
            指定資料庫路徑。
            未提供時使用預設開發資料庫。

    Returns:
        dict[str, Any] | None:
            找到資料時回傳字典，否則回傳 None。
    """

    normalized_code = code.strip().upper()

    if not normalized_code:
        return None

    connection = get_connection(database_path)

    try:
        row = connection.execute(
            f"""
            SELECT
                {ETF_SELECT_COLUMNS}
            FROM etf_master
            WHERE code = ?;
            """,
            (normalized_code,),
        ).fetchone()

        if row is None:
            return None

        return row_to_dictionary(row)

    finally:
        connection.close()