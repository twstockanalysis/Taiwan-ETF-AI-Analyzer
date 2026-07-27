"""系統路徑與資料庫設定。"""

from pathlib import Path


# settings.py 的位置：
# backend/app/config/settings.py
#
# parents[0] = config
# parents[1] = app
# parents[2] = backend
# parents[3] = 專案根目錄 TW-ETF-AI-Analyzer
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# SQLite 資料庫資料夾
DATABASE_DIR = PROJECT_ROOT / "database"

# SQLite 資料庫完整路徑
DATABASE_PATH = DATABASE_DIR / "tw_etf.db"