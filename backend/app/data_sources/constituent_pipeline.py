"""官方 ETF 成分股快照匯入流程。"""

from pathlib import Path

from backend.app.data_sources.yuanta_constituent_adapter import (
    fetch_yuanta_constituent_snapshot,
)
from backend.app.models.etf_constituent import ETFConstituentSnapshot
from backend.app.repositories.etf_constituent_repository import (
    save_constituent_snapshot,
)
from backend.app.repositories.etf_repository import get_etf_by_code


def import_yuanta_constituents(
    etf_code: str,
    database_path: str | Path,
) -> ETFConstituentSnapshot:
    """驗證 ETF 已存在後，下載並原子保存元大官方持股。"""

    normalized_code = etf_code.strip().upper()
    if get_etf_by_code(normalized_code, database_path) is None:
        raise ValueError(f"找不到 ETF：{normalized_code}")
    value = fetch_yuanta_constituent_snapshot(normalized_code)
    return save_constituent_snapshot(value, database_path)
