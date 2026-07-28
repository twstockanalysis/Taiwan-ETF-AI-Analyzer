"""FastAPI 共用 Dependency。"""

from pathlib import Path

from backend.app.config.settings import DATABASE_PATH


def get_database_path() -> Path:
    """取得目前 API 使用的資料庫路徑。

    Returns:
        Path: SQLite 資料庫路徑。
    """

    return DATABASE_PATH