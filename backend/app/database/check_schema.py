"""檢查 SQLite 資料表與欄位結構。"""

from backend.app.database.connection import get_connection


TABLE_NAME = "etf_master"


def table_exists() -> bool:
    """檢查 etf_master 資料表是否存在。

    Returns:
        bool: 資料表存在時回傳 True。
    """

    connection = get_connection()

    try:
        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?;
            """,
            (TABLE_NAME,),
        ).fetchone()

        return result is not None

    finally:
        connection.close()


def get_table_columns() -> list:
    """取得 etf_master 的欄位資訊。

    Returns:
        list: SQLite PRAGMA 回傳的欄位資料。
    """

    connection = get_connection()

    try:
        columns = connection.execute(
            f"PRAGMA table_info({TABLE_NAME});"
        ).fetchall()

        return columns

    finally:
        connection.close()


def main() -> None:
    """顯示資料表驗證結果。"""

    if not table_exists():
        print(f"資料表不存在：{TABLE_NAME}")
        print(
            "請先執行："
            "python -m backend.app.database.init_db"
        )
        return

    columns = get_table_columns()

    print(f"資料表存在：{TABLE_NAME}")
    print(f"欄位數量：{len(columns)}")
    print("-" * 70)

    for column in columns:
        primary_key = "是" if column["pk"] else "否"
        required = "是" if column["notnull"] else "否"

        print(
            f"欄位：{column['name']:<15}"
            f" 類型：{column['type']:<10}"
            f" 必填：{required:<2}"
            f" 主鍵：{primary_key}"
        )

    print("-" * 70)
    print("資料表結構檢查完成")


if __name__ == "__main__":
    main()