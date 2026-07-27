"""測試 SQLite 資料庫是否能正常連線。"""

from backend.app.config.settings import DATABASE_PATH
from backend.app.database.connection import get_connection


def main() -> None:
    """執行資料庫連線測試。"""

    connection = get_connection()

    try:
        result = connection.execute(
            "SELECT sqlite_version() AS version;"
        ).fetchone()

        print("SQLite 連線成功")
        print(f"資料庫版本：{result['version']}")
        print(f"資料庫位置：{DATABASE_PATH}")

    finally:
        connection.close()
        print("資料庫連線已關閉")


if __name__ == "__main__":
    main()