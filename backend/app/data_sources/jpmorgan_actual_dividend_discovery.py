"""摩根投信官方 ETF 配息實際配發 PDF 自動發現。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.issuer_landing_page_discovery import _AnchorParser
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


BASE_URL = "https://am.jpmorgan.com/"
ANNOUNCEMENT_URL = (
    "https://am.jpmorgan.com/tw/zh/asset-management/twetf/funds/announcements/"
)
SOURCE_ID = "jpmorgan_etf_dividend_document"
OFFICIAL_DOMAINS = ("jpmorgan.com", "am.jpmorgan.com")
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"(?<![0-9A-Z])([0-9]{4,6}[A-Z]?)(?![0-9A-Z])")


@dataclass(frozen=True, slots=True)
class JPMorganDividendCandidate:
    issuer_key: str
    etf_code: str
    document_id: str
    title: str
    document_url: str
    content_type: str = "application/pdf"
    information_basis: str = "UNKNOWN"


def parse_jpmorgan_dividend_documents(
    *, etf_code: str, html_text: str,
) -> tuple[JPMorganDividendCandidate, ...]:
    """依官方頁的 ETF 分組，只接受標示實際配發的 PDF。"""

    normalized_code = etf_code.strip().upper()
    parser = _AnchorParser()
    parser.feed(html_text)
    target_names: list[str] = []
    for _, title in parser.links:
        title_upper = title.upper()
        if normalized_code not in _ETF_CODE_PATTERN.findall(title_upper):
            continue
        name = re.sub(re.escape(normalized_code), "", title_upper, count=1)
        name = name.split("ETF", 1)[0].strip()
        if len(name) >= 4:
            target_names.append(name)
    candidates: list[JPMorganDividendCandidate] = []
    seen: set[str] = set()
    for href, title in parser.links:
        title_upper = title.upper()
        if (
            not any(name in title_upper for name in target_names)
            or "配息" not in title
            or "實際配發" not in title
        ):
            continue
        url = urljoin(BASE_URL, href.strip())
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in OFFICIAL_DOMAINS
            or not parsed.path.lower().endswith(".pdf")
            or url in seen
        ):
            continue
        seen.add(url)
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        candidates.append(JPMorganDividendCandidate(
            issuer_key="jpmorgan",
            etf_code=normalized_code,
            document_id=f"jpmorgan-dividend-{normalized_code}-{digest}",
            title=title,
            document_url=url,
        ))
    return tuple(candidates)


def discover_jpmorgan_dividend_documents(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[JPMorganDividendCandidate, ...]:
    """從摩根官方 ETF 公告頁發現實際配發 PDF。"""

    source = get_actual_dividend_source(SOURCE_ID)
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.get(
        ANNOUNCEMENT_URL,
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("摩根官方公告回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("摩根官方公告未回傳 HTML")
    return parse_jpmorgan_dividend_documents(
        etf_code=etf_code,
        html_text=response.text,
    )
