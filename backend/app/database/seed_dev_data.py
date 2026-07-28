"""建立 M5 開發測試資料。"""

from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database


DEVELOPMENT_ETFS = [
    (
        "DEV001",
        "開發測試被動式ETF",
        0,
        0,
        None,
        None,
        None,
    ),
    (
        "DEV002A",
        "開發測試主動式ETF",
        1,
        0,
        None,
        None,
        None,
    ),
]


def seed_development_data() -> int:
    """寫入開發用 ETF 示範資料。

    Returns:
        int: 本次處理的資料筆數。
    """

    database_path = initialize_database()
    connection = get_connection(database_path)

    try:
        connection.executemany(
            """
            INSERT INTO etf_master (
                code,
                name,
                is_active,
                is_bond,
                listing_date,
                fund_size,
                expense_ratio
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                is_active = excluded.is_active,
                is_bond = excluded.is_bond,
                listing_date = excluded.listing_date,
                fund_size = excluded.fund_size,
                expense_ratio = excluded.expense_ratio;
            """,
            DEVELOPMENT_ETFS,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return len(DEVELOPMENT_ETFS)


def main() -> None:
    """執行開發資料建立作業。"""

    record_count = seed_development_data()

    print("開發測試資料建立成功")
    print(f"處理筆數：{record_count}")


if __name__ == "__main__":
    main()