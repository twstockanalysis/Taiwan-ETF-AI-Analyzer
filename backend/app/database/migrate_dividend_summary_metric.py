"""建立單次配息摘要補充資料表。"""

from pathlib import Path

from backend.app.config.settings import (
    DATABASE_PATH,
)
from backend.app.database.connection import (
    get_connection,
)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS
etf_dividend_summary_metric (
    dividend_id INTEGER PRIMARY KEY,
    distribution_period TEXT
        CHECK (
            distribution_period IS NULL
            OR (
                length(distribution_period) = 6
                AND substr(distribution_period, 5, 1) = 'Q'
                AND substr(distribution_period, 6, 1)
                    IN ('1', '2', '3', '4')
            )
        ),
    distribution_period_source_id TEXT,
    yield_pct REAL
        CHECK (yield_pct IS NULL OR yield_pct >= 0),
    yield_basis TEXT
        CHECK (
            yield_basis IS NULL
            OR yield_basis IN ('OFFICIAL', 'CALCULATED')
        ),
    yield_source_id TEXT,
    reference_trade_date TEXT,
    reference_close_price REAL
        CHECK (
            reference_close_price IS NULL
            OR reference_close_price > 0
        ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (
            distribution_period IS NULL
            AND distribution_period_source_id IS NULL
        )
        OR (
            distribution_period IS NOT NULL
            AND distribution_period_source_id IS NOT NULL
            AND length(trim(distribution_period_source_id)) > 0
        )
    ),
    CHECK (
        (
            yield_pct IS NULL
            AND yield_basis IS NULL
            AND yield_source_id IS NULL
            AND reference_trade_date IS NULL
            AND reference_close_price IS NULL
        )
        OR (
            yield_pct IS NOT NULL
            AND yield_basis IS NOT NULL
            AND yield_source_id IS NOT NULL
            AND length(trim(yield_source_id)) > 0
        )
    ),
    CHECK (
        yield_basis IS NULL
        OR yield_basis = 'OFFICIAL'
        OR (
            reference_trade_date IS NOT NULL
            AND reference_close_price IS NOT NULL
        )
    ),
    CHECK (
        yield_basis IS NULL
        OR yield_basis = 'CALCULATED'
        OR (
            reference_trade_date IS NULL
            AND reference_close_price IS NULL
        )
    ),
    FOREIGN KEY (dividend_id)
        REFERENCES etf_dividend (id)
        ON DELETE CASCADE
);
"""


INDEX_SQL = """
CREATE INDEX IF NOT EXISTS
idx_etf_dividend_summary_yield_basis
ON etf_dividend_summary_metric (
    yield_basis,
    dividend_id
);
"""


def dividend_summary_metric_table_exists(
    database_path: str | Path | None = None,
) -> bool:
    """確認摘要補充資料表是否存在。"""

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = (
                  'etf_dividend_summary_metric'
              );
            """
        ).fetchone()

        return row is not None

    finally:
        connection.close()


def migrate_dividend_summary_metric(
    database_path: str | Path | None = None,
) -> bool:
    """建立摘要補充資料表及索引。"""

    resolved_path = (
        Path(database_path)
        if database_path is not None
        else DATABASE_PATH
    )

    existed_before = (
        dividend_summary_metric_table_exists(
            resolved_path
        )
    )

    connection = get_connection(
        resolved_path
    )

    try:
        connection.execute(
            "BEGIN IMMEDIATE;"
        )
        connection.execute(
            CREATE_TABLE_SQL
        )
        connection.execute(
            INDEX_SQL
        )
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return not existed_before


def main() -> None:
    """執行預設資料庫 Migration。"""

    changed = migrate_dividend_summary_metric()

    if changed:
        print(
            "etf_dividend_summary_metric "
            "Migration 完成"
        )

    else:
        print(
            "etf_dividend_summary_metric "
            "已存在，不需要 Migration"
        )


if __name__ == "__main__":
    main()
