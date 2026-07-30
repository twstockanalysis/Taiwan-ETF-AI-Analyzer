"""Upgrade ETF dividend components to basis-aware storage."""

from pathlib import Path
import sqlite3

from backend.app.config.settings import (
    DATABASE_PATH,
)
from backend.app.database.connection import (
    get_connection,
)


CURRENT_UNIQUE_COLUMNS = (
    "dividend_id",
    "component_basis",
    "component_code",
    "source_id",
)


NEW_COMPONENT_TABLE_SQL = """
CREATE TABLE etf_dividend_component_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    dividend_id INTEGER NOT NULL,

    component_code TEXT NOT NULL
        CHECK (
            length(trim(component_code)) > 0
        ),

    component_basis TEXT NOT NULL
        DEFAULT 'ACTUAL'
        CHECK (
            component_basis IN (
                'ESTIMATED',
                'ACTUAL'
            )
        ),

    component_name TEXT,

    amount_per_unit REAL,

    ratio_pct REAL,

    source_id TEXT NOT NULL
        CHECK (length(trim(source_id)) > 0),

    import_batch_id INTEGER,

    source_updated_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        amount_per_unit IS NOT NULL
        OR ratio_pct IS NOT NULL
    ),

    CHECK (
        amount_per_unit IS NULL
        OR amount_per_unit >= 0
    ),

    CHECK (
        ratio_pct IS NULL
        OR (
            ratio_pct >= 0
            AND ratio_pct <= 100
        )
    ),

    FOREIGN KEY (dividend_id)
        REFERENCES etf_dividend (id)
        ON DELETE CASCADE,

    FOREIGN KEY (import_batch_id)
        REFERENCES import_batch (id)
        ON DELETE SET NULL,

    UNIQUE (
        dividend_id,
        component_basis,
        component_code,
        source_id
    )
);
"""


INDEX_STATEMENTS = (
    """
    CREATE INDEX IF NOT EXISTS
    idx_etf_dividend_component_code
    ON etf_dividend_component (
        component_code,
        ratio_pct DESC
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS
    idx_etf_dividend_component_lookup
    ON etf_dividend_component (
        dividend_id,
        component_basis,
        component_code,
        source_id
    );
    """,
)


def dividend_component_table_exists(
    connection: sqlite3.Connection,
) -> bool:
    """Return whether the dividend-component table exists."""

    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'etf_dividend_component';
        """
    ).fetchone()

    return row is not None


def dividend_component_has_basis(
    connection: sqlite3.Connection,
) -> bool:
    """Return whether component_basis exists."""

    rows = connection.execute(
        """
        PRAGMA table_info(
            etf_dividend_component
        );
        """
    ).fetchall()

    return any(
        row["name"] == "component_basis"
        for row in rows
    )


def dividend_component_has_current_unique_key(
    connection: sqlite3.Connection,
) -> bool:
    """Return whether the expected unique key exists."""

    index_rows = connection.execute(
        """
        PRAGMA index_list(
            etf_dividend_component
        );
        """
    ).fetchall()

    for index_row in index_rows:
        if not index_row["unique"]:
            continue

        index_name = index_row["name"]

        column_rows = connection.execute(
            f"""
            PRAGMA index_info(
                "{index_name}"
            );
            """
        ).fetchall()

        columns = tuple(
            row["name"]
            for row in column_rows
        )

        if columns == CURRENT_UNIQUE_COLUMNS:
            return True

    return False


def dividend_component_schema_is_current(
    connection: sqlite3.Connection,
) -> bool:
    """Return whether the table uses the current schema."""

    return (
        dividend_component_has_basis(
            connection
        )
        and dividend_component_has_current_unique_key(
            connection
        )
    )


def ensure_component_indexes(
    connection: sqlite3.Connection,
) -> None:
    """Create the current lookup indexes."""

    for statement in INDEX_STATEMENTS:
        connection.execute(
            statement
        )


def migrate_dividend_component_basis(
    database_path: str | Path | None = None,
) -> bool:
    """Upgrade dividend components to basis-aware uniqueness.

    Existing component rows are preserved and classified as
    ACTUAL because older schema versions only supported actual
    source component codes such as 76W.

    Returns:
        bool:
            True when the table was rebuilt.
            False when no rebuild was needed.
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
        from backend.app.database.init_db import (
            initialize_database,
        )

        initialize_database(
            resolved_database_path
        )

        return False

    connection = get_connection(
        resolved_database_path
    )

    try:
        if not dividend_component_table_exists(
            connection
        ):
            connection.close()

            from backend.app.database.init_db import (
                initialize_database,
            )

            initialize_database(
                resolved_database_path
            )

            return False

        if dividend_component_schema_is_current(
            connection
        ):
            ensure_component_indexes(
                connection
            )
            connection.commit()

            return False

        has_basis = (
            dividend_component_has_basis(
                connection
            )
        )

        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        connection.execute(
            """
            DROP TABLE IF EXISTS
            etf_dividend_component_new;
            """
        )

        connection.execute(
            NEW_COMPONENT_TABLE_SQL
        )

        basis_expression = (
            """
            CASE
                WHEN component_basis IN (
                    'ESTIMATED',
                    'ACTUAL'
                )
                THEN component_basis
                ELSE 'ACTUAL'
            END
            """
            if has_basis
            else "'ACTUAL'"
        )

        connection.execute(
            f"""
            INSERT INTO etf_dividend_component_new (
                id,
                dividend_id,
                component_code,
                component_basis,
                component_name,
                amount_per_unit,
                ratio_pct,
                source_id,
                import_batch_id,
                source_updated_at,
                created_at,
                updated_at
            )
            SELECT
                id,
                dividend_id,
                component_code,
                {basis_expression},
                component_name,
                amount_per_unit,
                ratio_pct,
                source_id,
                import_batch_id,
                source_updated_at,
                created_at,
                updated_at
            FROM etf_dividend_component;
            """
        )

        connection.execute(
            """
            DROP TABLE etf_dividend_component;
            """
        )

        connection.execute(
            """
            ALTER TABLE
                etf_dividend_component_new
            RENAME TO
                etf_dividend_component;
            """
        )

        ensure_component_indexes(
            connection
        )

        violations = connection.execute(
            """
            PRAGMA foreign_key_check;
            """
        ).fetchall()

        if violations:
            raise RuntimeError(
                "配息組成 Migration 後出現"
                " Foreign Key 錯誤"
            )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        try:
            connection.close()
        except Exception:
            pass


def main() -> None:
    """Run the migration for the default database."""

    changed = migrate_dividend_component_basis()

    if changed:
        print(
            "etf_dividend_component Migration 完成"
        )
        print(
            "既有配息組成已設為 ACTUAL"
        )

    else:
        print(
            "etf_dividend_component 已是新版，"
            "不需要 Migration"
        )


if __name__ == "__main__":
    main()
