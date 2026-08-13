"""街口投信官方 ETF 收益分配資格 Adapter。"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "jko_etf_dividend_document"
MAX_RESPONSE_BYTES = 1_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_TAG_PATTERN = re.compile(r"<[^>]+>")
_DISTRIBUTION_PATTERN = re.compile(
    r"<td[^>]*>\s*收益分配\s*</td>\s*<td[^>]*>(.*?)</td>",
    re.I | re.S,
)


OFFICIAL_JKO_ETF_PAGES: dict[str, str] = {
    "00693U": "https://ec.jkoam.com/EventArea/promote-00693u.php",
    "00763U": "https://ec.jkoam.com/EventArea/promote-00763u.php",
    "00715L": "https://ec.jkoam.com/EventArea/promote-00715l.php",
}


@dataclass(frozen=True, slots=True)
class JKODividendEligibility:
    etf_code: str
    distributes_income: bool
    official_value: str
    source_url: str
    information_basis: str = "OFFICIAL_PRODUCT_TERMS"


def parse_jko_dividend_eligibility(
    *, etf_code: str, source_url: str, html_text: str,
) -> JKODividendEligibility:
    """解析官方產品條款中的收益分配狀態。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    match = _DISTRIBUTION_PATTERN.search(html_text)
    if match is None:
        raise ValueError(f"街口官方產品頁找不到收益分配欄位：{normalized}")
    value = re.sub(
        r"\s+", " ", html.unescape(_TAG_PATTERN.sub(" ", match.group(1))),
    ).strip()
    if value != "無":
        raise ValueError(f"街口 ETF 收益分配狀態需要重新驗證：{normalized}={value}")
    return JKODividendEligibility(
        etf_code=normalized,
        distributes_income=False,
        official_value=value,
        source_url=source_url,
    )


def fetch_jko_dividend_eligibility(
    *, etf_code: str, allow_network: bool = False,
) -> JKODividendEligibility:
    """依 ETF 代號讀取街口官方產品頁的收益分配資格。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    normalized = etf_code.strip().upper()
    try:
        url = OFFICIAL_JKO_ETF_PAGES[normalized]
    except KeyError as error:
        raise ValueError(f"尚未驗證街口 ETF 產品頁：{normalized}") from error
    source = get_actual_dividend_source(SOURCE_ID)
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.get(
        url,
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("街口投信官方產品頁超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("街口投信官方產品頁未回傳 HTML")
    response.encoding = "utf-8"
    return parse_jko_dividend_eligibility(
        etf_code=normalized,
        source_url=str(response.url),
        html_text=response.text,
    )
