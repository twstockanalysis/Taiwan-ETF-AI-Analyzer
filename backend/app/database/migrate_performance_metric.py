"""將既有 etf_performance 升級為多績效類型 Schema。"""

from pathlib import Path
import sqlite3

from backend.app.config.settings import (
    DATABASE_PATH,
)

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)


NEW_PERFORMANCE_TABLE_SQL = """
CREATE TABLE etf_performance_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    etf_code TEXT NOT NULL,

    as_of_date TEXT NOT NULL,

    period_code TEXT NOT NULL
        CHECK (
            period_code IN (
                '1D',
                '1W',
                '1M',
                '3M',
                '6M',
                '1Y',
                '3Y',
                '5Y'
            )
        ),

    metric_code TEXT NOT NULL
        DEFAULT 'PRICE_RETURN'
        CHECK (
            metric_code IN (
                'PRICE_RETURN',
                'TOTAL_RETURN',
                'NAV_RETURN'
            )
        ),

    return_pct REAL NOT NULL
        CHECK (return_pct >= -100),

    source_id TEXT NOT NULL
        CHECK (length(trim(source_id)) > 0),

    import_batch_id INTEGER,

    source_updated_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (etf_code)
        REFERENCES etf_master (code)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (import_batch_id)
        REFERENCES import_batch (id)
        ON DELETE SET NULL,

    UNIQUE (
        etf_code,
        as_of_date,
        period_code,
        metric_code,
        source_id
    )
);
"""


INDEX_STATEMENTS = (
    """
    CREATE INDEX IF NOT EXISTS
    idx_etf_performance_lookup
    ON etf_performance (
        metric_code,
        period_code,
        as_of_date DESC,
        return_pct DESC
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_etf_performance_code_date
    ON etf_performance (
        etf_code,
        metric_code,
        period_code,
        as_of_date DESC
    );
    """,
)


def performance_table_has_metric_code(
    connection: sqlite3.Connection,
) -> bool:
    """確認績效表是否已存在 metric_code。"""

    rows = connection.execute(
        """
        PRAGMA table_info(
            etf_performance
        );
        """
    ).fetchall()

    return any(
        row["name"] == "metric_code"
        for row in rows
    )


def migrate_performance_metric(
    database_path: str | Path | None = None,
) -> bool:
    """升級 ETF 績效表。

    舊有績效資料會被標記為：

        metric_code = PRICE_RETURN

    Returns:
        bool:
            True 代表本次執行了 Migration；
            False 代表資料庫已是新版。
    """

    resolved_database_path = (
        Path(database_path)
        if database_path is not None
        else DATABASE_PATH
    )

    resolved_database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not resolved_database_path.exists():
        initialize_database(
            resolved_database_path
        )
        return False

    connection = get_connection(
        resolved_database_path
    )

    try:
        if performance_table_has_metric_code(
            connection
        ):
            return False

        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        connection.execute(
            """
            DROP TABLE IF EXISTS
            etf_performance_new;
            """
        )

        connection.execute(
            NEW_PERFORMANCE_TABLE_SQL
        )

        connection.execute(
            """
            INSERT INTO etf_performance_new (
                id,
                etf_code,
                as_of_date,
                period_code,
                metric_code,
                return_pct,
                source_id,
                import_batch_id,
                source_updated_at,
                created_at,
                updated_at
            )
            SELECT
                id,
                etf_code,
                as_of_date,
                period_code,
                'PRICE_RETURN',
                return_pct,
                source_id,
                import_batch_id,
                source_updated_at,
                created_at,
                updated_at
            FROM etf_performance;
            """
        )

        connection.execute(
            """
            DROP TABLE etf_performance;
            """
        )

        connection.execute(
            """
            ALTER TABLE
                etf_performance_new
            RENAME TO
                etf_performance;
            """
        )

        for statement in INDEX_STATEMENTS:
            connection.execute(
                statement
            )

        violations = connection.execute(
            """
            PRAGMA foreign_key_check;
            """
        ).fetchall()

        if violations:
            raise RuntimeError(
                "績效表 Migration 後出現"
                " Foreign Key 錯誤"
            )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def main() -> None:
    """執行 Migration。"""

    changed = migrate_performance_metric()

    if changed:
        print(
            "etf_performance Migration 完成"
        )
        print(
            "既有績效已設為 PRICE_RETURN"
        )

    else:
        print(
            "etf_performance 已是新版，"
            "不需要 Migration"
        )


if __name__ == "__main__":
    main()