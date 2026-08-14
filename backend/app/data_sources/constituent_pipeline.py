"""官方 ETF 成分股快照匯入流程。"""

from pathlib import Path

from backend.app.data_sources.direct_constituent_adapters import (
    DIRECT_CONSTITUENT_FETCHERS,
)
from backend.app.data_sources.mapped_constituent_adapters import (
    MAPPED_CONSTITUENT_FETCHERS,
)
from backend.app.data_sources.session_constituent_adapters import (
    SESSION_CONSTITUENT_FETCHERS,
)
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


def import_official_constituents(
    issuer_key: str,
    etf_code: str,
    database_path: str | Path,
) -> ETFConstituentSnapshot:
    """以統一介面匯入已自動化投信的官方成分股。"""

    normalized_issuer = issuer_key.strip().lower()
    normalized_code = etf_code.strip().upper()
    if get_etf_by_code(normalized_code, database_path) is None:
        raise ValueError(f"找不到 ETF：{normalized_code}")
    if normalized_issuer == "yuanta":
        value = fetch_yuanta_constituent_snapshot(normalized_code)
    else:
        fetcher = (
            DIRECT_CONSTITUENT_FETCHERS.get(normalized_issuer)
            or MAPPED_CONSTITUENT_FETCHERS.get(normalized_issuer)
            or SESSION_CONSTITUENT_FETCHERS.get(normalized_issuer)
        )
        if fetcher is None:
            raise ValueError(f"尚未支援投信成分股自動匯入：{normalized_issuer}")
        value = fetcher(normalized_code)
    return save_constituent_snapshot(value, database_path)
