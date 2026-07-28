"""ETF 主資料匯入 Repository。"""

from dataclasses import dataclass
from pathlib import Path

from backend.app.database.connection import get_connection
from backend.app.models.etf_import import ETFImportRecord


DEVELOPMENT_ETF_CODES = (
    "DEV001",
    "DEV002A",
)


@dataclass(
    frozen=True,
    slots=True,
)
class ETFImportSummary:
    """ETF 主資料匯入結果。"""

    total_records: int
    inserted_records: int
    updated_records: int
    deleted_development_records: int


def validate_unique_codes(
    records: list[ETFImportRecord],
) -> None:
    """確認匯入資料不存在重複 ETF 代號。

    Args:
        records:
            準備匯入的 ETF 資料。

    Raises:
        ValueError:
            發現重複 ETF 代號時拋出。
    """

    seen_codes: set[str] = set()
    duplicate_codes: set[str] = set()

    for record in records:
        if record.code in seen_codes:
            duplicate_codes.add(record.code)

        seen_codes.add(record.code)

    if duplicate_codes:
        duplicate_text = ", ".join(
            sorted(duplicate_codes)
        )

        raise ValueError(
            f"匯入資料包含重複 ETF 代號："
            f"{duplicate_text}"
        )


def upsert_etf_master(
    records: list[ETFImportRecord],
    database_path: str | Path | None = None,
    remove_development_records: bool = True,
) -> ETFImportSummary:
    """新增或更新 ETF 主資料。

    Args:
        records:
            已正規化及驗證的 ETF 資料。
        database_path:
            指定 SQLite 資料庫路徑。
        remove_development_records:
            是否移除 M5 開發測試資料。

    Returns:
        ETFImportSummary:
            新增、更新與刪除筆數。

    Raises:
        ValueError:
            匯入資料代號重複時拋出。
    """

    validate_unique_codes(records)

    connection = get_connection(
        database_path
    )

    try:
        existing_rows = connection.execute(
            """
            SELECT code
            FROM etf_master;
            """
        ).fetchall()

        existing_codes = {
            row["code"]
            for row in existing_rows
        }

        incoming_codes = {
            record.code
            for record in records
        }

        inserted_records = len(
            incoming_codes - existing_codes
        )

        updated_records = len(
            incoming_codes & existing_codes
        )

        deleted_development_records = 0

        if remove_development_records:
            placeholders = ", ".join(
                "?"
                for _ in DEVELOPMENT_ETF_CODES
            )

            cursor = connection.execute(
                f"""
                DELETE FROM etf_master
                WHERE code IN ({placeholders});
                """,
                DEVELOPMENT_ETF_CODES,
            )

            deleted_development_records = (
                cursor.rowcount
            )

        connection.executemany(
            """
            INSERT INTO etf_master (
                code,
                name,
                is_active,
                is_bond,
                listing_date
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                is_active = excluded.is_active,
                is_bond = excluded.is_bond,
                listing_date = excluded.listing_date;
            """,
            [
                (
                    record.code,
                    record.name,
                    int(record.is_active),
                    int(record.is_bond),
                    (
                        record.listing_date.isoformat()
                        if record.listing_date
                        else None
                    ),
                )
                for record in records
            ],
        )

        connection.commit()

        return ETFImportSummary(
            total_records=len(records),
            inserted_records=inserted_records,
            updated_records=updated_records,
            deleted_development_records=(
                deleted_development_records
            ),
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()