"""富邦投信 ETF 官方收益分配文件自動發現。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "fubon_etf_dividend_document"
FUND_LIST_URL = (
    "https://www.fubon.com/asset-management/fund/info/by_nav?type=FundByNav"
)
FUND_DETAIL_URL = "https://www.fubon.com/asset-management/fund/info/fund?Fd={fund_id}"
MAX_RESPONSE_BYTES = 3_000_000
MAX_DOCUMENTS = 20
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_DATE_PATTERN = re.compile(r"(20\d{2})/(\d{2})/(\d{2})")


@dataclass(frozen=True, slots=True)
class FubonDividendDocumentCandidate:
    etf_code: str
    source_id: str
    document_id: str
    title: str
    declared_date: date
    document_url: str
    content_type: str = "application/pdf"
    information_basis: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class FubonDividendDiscoveryResult:
    etf_code: str
    fund_id: str
    candidates: tuple[FubonDividendDocumentCandidate, ...]


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((
                self._href,
                re.sub(r"\s+", " ", " ".join(self._text)).strip(),
            ))
            self._href = None
            self._text = []


def normalize_fubon_etf_code(etf_code: str) -> str:
    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    return normalized


def resolve_fubon_fund_id(html_text: str, etf_code: str) -> str:
    """從富邦官方基金總覽解析證券代號對應的 Fd。"""

    normalized = normalize_fubon_etf_code(etf_code)
    parser = _AnchorParser()
    parser.feed(html_text)
    for href, _ in parser.links:
        parsed = urlsplit(urljoin(FUND_LIST_URL, href))
        fund_ids = parse_qs(parsed.query).get("Fd", [])
        if not fund_ids:
            continue
        anchor_end = html_text.find("</a>", html_text.find(href))
        next_anchor = html_text.find("<a ", anchor_end + 4)
        block = html_text[anchor_end:next_anchor if next_anchor >= 0 else None]
        if normalized in re.sub(r"\s+", "", block).upper():
            fund_id = fund_ids[0].strip()
            if re.fullmatch(r"[0-9A-Z]{1,10}", fund_id):
                return fund_id
    raise ValueError(f"富邦官方基金總覽找不到 ETF：{normalized}")


def parse_fubon_dividend_documents(
    *, html_text: str, etf_code: str, max_documents: int = MAX_DOCUMENTS,
) -> tuple[FubonDividendDocumentCandidate, ...]:
    """解析基金頁的官方收益分配 PDF，不推論期前或期後。"""

    normalized = normalize_fubon_etf_code(etf_code)
    if max_documents < 1 or max_documents > MAX_DOCUMENTS:
        raise ValueError(f"max_documents 必須介於 1 與 {MAX_DOCUMENTS}")
    source = get_actual_dividend_source(SOURCE_ID)
    parser = _AnchorParser()
    parser.feed(html_text)
    candidates: list[FubonDividendDocumentCandidate] = []
    for href, title in parser.links:
        url = urljoin(FUND_DETAIL_URL, href.strip())
        if (
            "etrade.fsit.com.tw/case/news/fund_service/" not in url.lower()
            or not url.lower().endswith(".pdf")
            or "收益分配公告" not in title
            or "期前公告" in title
        ):
            continue
        match = _DATE_PATTERN.search(title)
        if match is None:
            continue
        validate_official_source_url(source, url)
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        candidates.append(FubonDividendDocumentCandidate(
            etf_code=normalized,
            source_id=SOURCE_ID,
            document_id=f"fubon-dividend-{normalized}-{digest}",
            title=title.lstrip("‧ "),
            declared_date=date(*(int(value) for value in match.groups())),
            document_url=url,
        ))
        if len(candidates) >= max_documents:
            break
    return tuple(candidates)


def _fetch(url: str, *, allow_network: bool) -> str:
    source = get_actual_dividend_source(SOURCE_ID)
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.get(
        url, timeout=30.0, follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("富邦官方回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("富邦官方查詢回傳非 HTML 內容")
    return response.text


def discover_fubon_dividend_documents(
    *, etf_code: str, allow_network: bool = False,
) -> FubonDividendDiscoveryResult:
    normalized = normalize_fubon_etf_code(etf_code)
    fund_id = resolve_fubon_fund_id(
        _fetch(FUND_LIST_URL, allow_network=allow_network), normalized
    )
    detail_url = FUND_DETAIL_URL.format(fund_id=fund_id)
    candidates = parse_fubon_dividend_documents(
        html_text=_fetch(detail_url, allow_network=allow_network),
        etf_code=normalized,
    )
    return FubonDividendDiscoveryResult(normalized, fund_id, candidates)
