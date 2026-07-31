"""初始化 TW ETF AI Analyzer SQLite 資料庫。"""

from pathlib import Path

from backend.app.config.settings import DATABASE_PATH
from backend.app.database.connection import get_connection


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def load_schema() -> str:
    """讀取 schema.sql 內容。"""

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"找不到資料庫 Schema：{SCHEMA_PATH}"
        )

    return SCHEMA_PATH.read_text(
        encoding="utf-8"
    )


def legacy_performance_requires_migration(
    database_path: Path,
) -> bool:
    """判斷既有績效表是否早於 metric_code Schema。

    舊版資料庫若直接執行目前 schema.sql，建立績效索引時
    會先引用尚不存在的 metric_code。因此必須先完成該表
    Migration，再執行完整 Schema。
    """

    if not database_path.exists():
        return False

    connection = get_connection(
        database_path
    )

    try:
        table_row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'etf_performance';
            """
        ).fetchone()

        if table_row is None:
            return False

        columns = connection.execute(
            """
            PRAGMA table_info(
                etf_performance
            );
            """
        ).fetchall()

        return not any(
            row["name"] == "metric_code"
            for row in columns
        )

    finally:
        connection.close()


def initialize_database(
    database_path: str | Path | None = None,
) -> Path:
    """建立或升級 SQLite 資料庫及資料表。"""

    target_path = (
        DATABASE_PATH
        if database_path is None
        else Path(database_path)
    )

    target_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if legacy_performance_requires_migration(
        target_path
    ):
        from backend.app.database.migrate_performance_metric import (
            migrate_performance_metric,
        )

        migrate_performance_metric(
            target_path
        )

    schema_sql = load_schema()
    connection = get_connection(
        target_path
    )

    try:
        connection.executescript(
            schema_sql
        )
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    from backend.app.database.migrate_performance_metric import (
        migrate_performance_metric,
    )

    migrate_performance_metric(
        target_path
    )

    from backend.app.database.migrate_dividend_component_basis import (
        migrate_dividend_component_basis,
    )

    migrate_dividend_component_basis(
        target_path
    )

    from backend.app.database.migrate_dividend_source_document import (
        migrate_dividend_source_document,
    )

    migrate_dividend_source_document(
        target_path
    )

    from backend.app.database.migrate_dividend_review_queue import (
        migrate_dividend_review_queue,
    )

    migrate_dividend_review_queue(
        target_path
    )

    return target_path


def main() -> None:
    """執行預設資料庫初始化。"""

    database_path = initialize_database()

    print("資料庫初始化成功")
    print(f"Schema 檔案：{SCHEMA_PATH}")
    print(f"資料庫位置：{database_path}")
    print("資料庫連線已關閉")


if __name__ == "__main__":
    main()
