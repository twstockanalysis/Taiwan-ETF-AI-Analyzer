"""將既有手動價格持股表升級為可保存官方價格來源與缺值。"""

from pathlib import Path

from backend.app.database.connection import get_connection


def migrate_manual_holding_market_price(
    database_path: str | Path,
) -> bool:
    connection = get_connection(database_path)
    try:
        table = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'manual_holding';
            """
        ).fetchone()
        if table is None:
            return False

        columns = connection.execute(
            "PRAGMA table_info(manual_holding);"
        ).fetchall()
        by_name = {row["name"]: row for row in columns}
        if (
            "price_source_id" in by_name
            and not bool(by_name["unit_price"]["notnull"])
        ):
            return False

        connection.executescript(
            """
            PRAGMA foreign_keys = OFF;

            CREATE TABLE manual_holding_m11_5 (
                etf_code TEXT PRIMARY KEY,
                held_units INTEGER NOT NULL CHECK (held_units > 0),
                unit_price REAL CHECK (unit_price IS NULL OR unit_price > 0),
                price_as_of_date TEXT,
                price_source_id TEXT,
                currency TEXT NOT NULL DEFAULT 'TWD' CHECK (currency = 'TWD'),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK (
                    (unit_price IS NULL
                        AND price_as_of_date IS NULL
                        AND price_source_id IS NULL)
                    OR unit_price IS NOT NULL
                ),
                FOREIGN KEY (etf_code) REFERENCES etf_master (code)
                    ON UPDATE CASCADE ON DELETE CASCADE
            );

            INSERT INTO manual_holding_m11_5 (
                etf_code, held_units, unit_price, price_as_of_date,
                price_source_id, currency, created_at, updated_at
            )
            SELECT
                etf_code, held_units, unit_price, price_as_of_date,
                CASE WHEN unit_price IS NOT NULL THEN 'manual_legacy' END,
                currency, created_at, updated_at
            FROM manual_holding;

            DROP TABLE manual_holding;
            ALTER TABLE manual_holding_m11_5 RENAME TO manual_holding;

            CREATE INDEX idx_manual_holding_updated
            ON manual_holding (updated_at DESC, etf_code);

            PRAGMA foreign_keys = ON;
            """
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
