"""系統路徑與資料庫設定。"""

from pathlib import Path


# 專案根目錄:
# TW-ETF-AI-Analyzer/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# SQLite 資料庫資料夾
DATABASE_DIR = PROJECT_ROOT / "database"

# SQLite 資料庫完整路徑
DATABASE_PATH = DATABASE_DIR / "tw_etf.db"

# ETF 資料處理目錄
DATA_DIR = PROJECT_ROOT / "data"

# 官方來源下載的原始資料
RAW_DATA_DIR = DATA_DIR / "raw"

# 正規化後的資料
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# 驗證失敗的資料
REJECTED_DATA_DIR = DATA_DIR / "rejected"