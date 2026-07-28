"""SQLite 資料庫連線模組。"""

import sqlite3
from pathlib import Path

from backend.app.config.settings import DATABASE_PATH


def get_connection(
    database_path: str | Path | None = None,
) -> sqlite3.Connection:
    """建立並回傳 SQLite 資料庫連線。

    Args:
        database_path:
            指定資料庫路徑。
            未提供時使用系統預設資料庫。

    Returns:
        sqlite3.Connection: SQLite 資料庫連線物件。
    """

    if database_path is None:
        target_path = DATABASE_PATH
    else:
        target_path = Path(database_path)

    # 如果資料庫所在資料夾不存在，自動建立。
    target_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 建立 SQLite 資料庫連線。
    connection = sqlite3.connect(
        str(target_path)
    )

    # 允許使用欄位名稱讀取查詢結果。
    connection.row_factory = sqlite3.Row

    # 每次建立連線時啟用外鍵約束。
    connection.execute(
        "PRAGMA foreign_keys = ON;"
    )

    return connection