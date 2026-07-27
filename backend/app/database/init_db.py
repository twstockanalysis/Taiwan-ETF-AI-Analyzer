"""初始化 TW ETF AI Analyzer SQLite 資料庫。"""

from pathlib import Path

from backend.app.config.settings import DATABASE_PATH
from backend.app.database.connection import get_connection


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def load_schema() -> str:
    """讀取 schema.sql 內容。

    Returns:
        str: 完整的 SQL Schema。

    Raises:
        FileNotFoundError: 找不到 schema.sql 時拋出。
    """

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"找不到資料庫 Schema：{SCHEMA_PATH}"
        )

    return SCHEMA_PATH.read_text(encoding="utf-8")


def initialize_database() -> None:
    """建立資料庫及資料表。"""

    schema_sql = load_schema()
    connection = get_connection()

    try:
        connection.executescript(schema_sql)
        connection.commit()

        print("資料庫初始化成功")
        print(f"Schema 檔案：{SCHEMA_PATH}")
        print(f"資料庫位置：{DATABASE_PATH}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
        print("資料庫連線已關閉")


def main() -> None:
    """執行資料庫初始化。"""

    initialize_database()


if __name__ == "__main__":
    main()