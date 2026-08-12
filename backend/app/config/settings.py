"""系統路徑與資料庫設定。"""

import os
from collections.abc import Mapping
from pathlib import Path


# 專案根目錄:
# TW-ETF-AI-Analyzer/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# SQLite 資料庫資料夾（本機開發預設）
DATABASE_DIR = PROJECT_ROOT / "database"

DATABASE_PATH_ENV = "TW_ETF_DATABASE_PATH"


def resolve_database_path(
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Resolve the database path, rejecting ambiguous relative deployment paths."""

    values = os.environ if environ is None else environ
    configured = values.get(DATABASE_PATH_ENV, "").strip()
    if not configured:
        return DATABASE_DIR / "tw_etf.db"
    path = Path(configured).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{DATABASE_PATH_ENV} 必須是絕對路徑：{configured}")
    return path.resolve()


# Production must set TW_ETF_DATABASE_PATH to storage outside the release tree.
DATABASE_PATH = resolve_database_path()

# ETF 資料處理目錄
DATA_DIR = PROJECT_ROOT / "data"

# 官方來源下載的原始資料
RAW_DATA_DIR = DATA_DIR / "raw"

# 正規化後的資料
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# 驗證失敗的資料
REJECTED_DATA_DIR = DATA_DIR / "rejected"
