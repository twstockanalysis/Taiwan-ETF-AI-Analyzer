"""SQLite 資料庫連線模組。"""

import sqlite3

from backend.app.config.settings import DATABASE_DIR, DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """建立並回傳 SQLite 資料庫連線。

    Returns:
        sqlite3.Connection: SQLite 資料庫連線物件。
    """

    # 如果 database 資料夾不存在，就自動建立。
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    # 建立 SQLite 資料庫連線。
    connection = sqlite3.connect(str(DATABASE_PATH))

    # 查詢結果可以使用欄位名稱讀取。
    connection.row_factory = sqlite3.Row

    # SQLite 預設不會強制執行外鍵約束，因此每次連線都要開啟。
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection