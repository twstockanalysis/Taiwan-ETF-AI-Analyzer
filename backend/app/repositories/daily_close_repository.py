"""ETF 官方每日收盤價 Repository。"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from backend.app.database.connection import get_connection
from backend.app.models.etf_price import ETFDailyCloseRecord


@dataclass(frozen=True, slots=True)
class DailyCloseUpsertSummary:
    total_records: int
    inserted_records: int
    updated_records: int


def upsert_daily_close_records(
    records: Iterable[ETFDailyCloseRecord],
    database_path: str | Path | None = None,
) -> DailyCloseUpsertSummary:
    """保存官方日收盤價；相同 ETF、日期與來源可安全重跑。"""

    unique_records = {
        (
            record.etf_code,
            record.trade_date.isoformat(),
            record.source_id,
        ): record
        for record in records
    }
    if not unique_records:
        return DailyCloseUpsertSummary(0, 0, 0)

    keys = set(unique_records)
    connection = get_connection(database_path)
    try:
        existing = {
            (row["etf_code"], row["trade_date"], row["source_id"])
            for row in connection.execute(
                """
                SELECT etf_code, trade_date, source_id
                FROM etf_daily_close;
                """
            ).fetchall()
        }
        connection.executemany(
            """
            INSERT INTO etf_daily_close (
                etf_code, trade_date, close_price, source_id
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(etf_code, trade_date, source_id) DO UPDATE SET
                close_price = excluded.close_price,
                updated_at = CURRENT_TIMESTAMP;
            """,
            [
                (
                    record.etf_code,
                    record.trade_date.isoformat(),
                    str(record.close_price),
                    record.source_id,
                )
                for record in unique_records.values()
            ],
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return DailyCloseUpsertSummary(
        total_records=len(keys),
        inserted_records=len(keys - existing),
        updated_records=len(keys & existing),
    )


def get_latest_daily_close(
    etf_code: str,
    database_path: str | Path | None = None,
) -> dict | None:
    """取得一檔 ETF 最新已保存的官方收盤價。"""

    normalized_code = etf_code.strip().upper()
    if not normalized_code:
        raise ValueError("etf_code 不得為空白")

    connection = get_connection(database_path)
    try:
        row = connection.execute(
            """
            SELECT etf_code, trade_date, close_price, source_id
            FROM etf_daily_close
            WHERE etf_code = ?
            ORDER BY trade_date DESC, source_id
            LIMIT 1;
            """,
            (normalized_code,),
        ).fetchone()
        if row is None:
            return None
        return {
            **dict(row),
            "close_price": Decimal(str(row["close_price"])),
        }
    finally:
        connection.close()


def list_daily_closes(
    etf_code: str,
    database_path: str | Path | None = None,
) -> list[dict]:
    """依日期列出一檔 ETF 的已保存官方收盤價。"""

    normalized_code = etf_code.strip().upper()
    connection = get_connection(database_path)
    try:
        rows = connection.execute(
            """
            SELECT etf_code, trade_date, close_price, source_id
            FROM etf_daily_close
            WHERE etf_code = ?
            ORDER BY trade_date;
            """,
            (normalized_code,),
        ).fetchall()
        return [
            {**dict(row), "close_price": Decimal(str(row["close_price"]))}
            for row in rows
        ]
    finally:
        connection.close()
