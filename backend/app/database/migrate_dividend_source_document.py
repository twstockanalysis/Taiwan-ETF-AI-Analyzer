"""建立正式配息來源文件資料表。"""

from pathlib import Path

from backend.app.config.settings import (
    DATABASE_PATH,
)
from backend.app.database.connection import (
    get_connection,
)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS
dividend_source_document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    source_id TEXT NOT NULL
        CHECK (length(trim(source_id)) > 0),

    source_document_id TEXT NOT NULL
        CHECK (
            length(trim(source_document_id)) > 0
        ),

    version_number INTEGER NOT NULL
        CHECK (version_number >= 1),

    source_url TEXT NOT NULL
        CHECK (length(trim(source_url)) > 0),

    source_document_date TEXT,

    downloaded_at TEXT NOT NULL,

    content_type TEXT NOT NULL
        CHECK (length(trim(content_type)) > 0),

    information_basis TEXT NOT NULL
        DEFAULT 'UNKNOWN'
        CHECK (
            information_basis IN (
                'UNKNOWN',
                'ACTUAL',
                'ESTIMATED'
            )
        ),

    checksum_sha256 TEXT NOT NULL
        CHECK (length(checksum_sha256) = 64),

    snapshot_path TEXT NOT NULL
        CHECK (
            length(trim(snapshot_path)) > 0
        ),

    metadata_path TEXT NOT NULL
        CHECK (
            length(trim(metadata_path)) > 0
        ),

    parse_status TEXT NOT NULL
        DEFAULT 'downloaded'
        CHECK (
            parse_status IN (
                'downloaded',
                'parsed',
                'rejected',
                'failed'
            )
        ),

    parse_error TEXT,

    import_batch_id INTEGER,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (import_batch_id)
        REFERENCES import_batch (id)
        ON DELETE SET NULL,

    UNIQUE (
        source_id,
        source_document_id,
        version_number
    ),

    UNIQUE (
        source_id,
        source_document_id,
        checksum_sha256
    )
);
"""


INDEX_STATEMENTS = (
    """
    CREATE INDEX IF NOT EXISTS
    idx_dividend_source_document_lookup
    ON dividend_source_document (
        source_id,
        source_document_id,
        version_number DESC
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_dividend_source_document_status
    ON dividend_source_document (
        parse_status,
        downloaded_at DESC
    );
    """,
)


def source_document_table_exists(
    database_path: str | Path | None = None,
) -> bool:
    """確認正式來源文件資料表是否存在。"""

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
                  'dividend_source_document'
              );
            """
        ).fetchone()

        return row is not None

    finally:
        connection.close()


def migrate_dividend_source_document(
    database_path: str | Path | None = None,
) -> bool:
    """建立來源文件資料表與索引。

    Returns:
        bool:
            True 代表本次建立資料表；
            False 代表資料表原本已存在。
    """

    resolved_path = (
        Path(database_path)
        if database_path is not None
        else DATABASE_PATH
    )

    existed_before = (
        source_document_table_exists(
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
        migrate_dividend_source_document()
    )

    if changed:
        print(
            "dividend_source_document "
            "Migration 完成"
        )

    else:
        print(
            "dividend_source_document "
            "已存在，不需要 Migration"
        )


if __name__ == "__main__":
    main()
