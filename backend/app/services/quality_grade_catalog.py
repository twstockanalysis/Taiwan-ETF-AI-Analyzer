"""建立可供公開探索頁共用、具資料庫失效鍵的歷史品質評等目錄。"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.app.models.market_eligibility import MarketEligibilityIndexRequest
from backend.app.services.market_eligibility_index import (
    build_market_eligibility_index,
)


DEFAULT_PUBLIC_GRADE_HISTORY_YEARS = 3


def normalize_quality_grade_codes(raw_codes: str) -> list[str]:
    """正規化 1 至 100 個不重複 ETF 代號。"""

    codes = [item.strip().upper() for item in raw_codes.split(",")]
    if not codes or any(not code or len(code) > 10 for code in codes):
        raise ValueError("ETF 代號格式不正確")
    normalized = list(dict.fromkeys(codes))
    if len(normalized) > 100:
        raise ValueError("單次最多查詢 100 檔 ETF 評等")
    return normalized


@lru_cache(maxsize=8)
def _cached_quality_grade_catalog(
    database_path: str,
    database_mtime_ns: int,
    database_size: int,
    analysis_date_iso: str,
    history_years: int,
) -> tuple[tuple[str, dict[str, Any]], ...]:
    """資料庫檔案變動或分析日改變時自動建立新的目錄。"""

    del database_mtime_ns, database_size
    request = MarketEligibilityIndexRequest(
        target_after_tax_cash_twd=0,
        target_months=list(range(1, 13)),
        existing_holdings=[],
        history_years=history_years,
        cash_deduction_rate_pct=0,
    )
    built = build_market_eligibility_index(
        request,
        database_path,
        as_of_date=date.fromisoformat(analysis_date_iso),
    )
    return tuple(
        (
            item.etf_code,
            item.historical_quality_grade.model_dump(mode="json"),
        )
        for item in built.response.candidates
    )

def build_quality_grade_catalog(
    database_path: str | Path,
    *,
    as_of_date: date | None = None,
    history_years: int = DEFAULT_PUBLIC_GRADE_HISTORY_YEARS,
) -> dict[str, dict[str, Any]]:
    """回傳全市場公開安全評等，不含原始分數、排名或可信度。"""

    resolved_path = Path(database_path).resolve()
    stat = resolved_path.stat()
    analysis_date = as_of_date or date.today()
    return dict(
        _cached_quality_grade_catalog(
            str(resolved_path),
            stat.st_mtime_ns,
            stat.st_size,
            analysis_date.isoformat(),
            history_years,
        )
    )
