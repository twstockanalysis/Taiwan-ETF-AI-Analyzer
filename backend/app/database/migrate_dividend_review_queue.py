"""建立正式配息來源審核佇列資料表。"""

from pathlib import Path

from backend.app.config.settings import (
    DATABASE_PATH,
)
from backend.app.database.connection import (
    get_connection,
)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS
dividend_source_review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    dividend_id INTEGER NOT NULL,

    issue_type TEXT NOT NULL
        CHECK (
            issue_type IN (
                'MISSING_ACTUAL_COMPONENTS',
                'MISSING_SOURCE_DOCUMENT'
            )
        ),

    suggested_source_id TEXT,

    priority INTEGER NOT NULL
        DEFAULT 50
        CHECK (
            priority >= 1
            AND priority <= 100
        ),

    status TEXT NOT NULL
        DEFAULT 'PENDING'
        CHECK (
            status IN (
                'PENDING',
                'IN_REVIEW',
                'RESOLVED',
                'SKIPPED'
            )
        ),

    notes TEXT,

    resolution_document_id INTEGER,

    last_evaluated_at TEXT NOT NULL,

    resolved_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (dividend_id)
        REFERENCES etf_dividend (id)
        ON DELETE CASCADE,

    FOREIGN KEY (resolution_document_id)
        REFERENCES dividend_source_document (id)
        ON DELETE SET NULL,

    UNIQUE (
        dividend_id,
        issue_type
    )
);
"""


INDEX_STATEMENTS = (
    """
    CREATE INDEX IF NOT EXISTS
    idx_dividend_review_queue_status
    ON dividend_source_review_queue (
        status,
        priority,
        updated_at DESC
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_dividend_review_queue_issue
    ON dividend_source_review_queue (
        issue_type,
        status,
        priority
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_dividend_review_queue_dividend
    ON dividend_source_review_queue (
        dividend_id,
        issue_type
    );
    """,
)


def review_queue_table_exists(
    database_path: str | Path | None = None,
) -> bool:
    """確認正式配息審核佇列表是否存在。"""

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
                  'dividend_source_review_queue'
              );
            """
        ).fetchone()

        return row is not None

    finally:
        connection.close()


def migrate_dividend_review_queue(
    database_path: str | Path | None = None,
) -> bool:
    """建立正式配息審核佇列表與索引。"""

    resolved_path = (
        Path(database_path)
        if database_path is not None
        else DATABASE_PATH
    )

    existed_before = (
        review_queue_table_exists(
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

        for statement in INDEX_STATEMENTS:
            connection.execute(
                statement
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

    changed = (
        migrate_dividend_review_queue()
    )

    if changed:
        print(
            "dividend_source_review_queue "
            "Migration 完成"
        )

    else:
        print(
            "dividend_source_review_queue "
            "已存在，不需要 Migration"
        )


if __name__ == "__main__":
    main()
