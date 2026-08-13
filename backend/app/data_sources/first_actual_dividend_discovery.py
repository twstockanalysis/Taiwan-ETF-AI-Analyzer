"""第一金投信官方 ETF 實際配息公告發現器。"""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "first_etf_dividend_document"
FUND_DATA_URL = "https://www.fsitc.com.tw/FundDetail.aspx?ID=D72"
NOTICE_URL = "https://www.fsitc.com.tw/ImportantNotice.aspx"
MAX_RESPONSE_BYTES = 6_000_000
MAX_DOCUMENTS = 50
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_FUND_PAIR_PATTERN = re.compile(
    r'"cName"\s*:\s*"([^"]+)"(?:(?!"cName").)*?'
    r'"cETFStockCode"\s*:\s*"([0-9A-Z]+)"',
    re.S,
)
_DATE_PATTERN = re.compile(r"(20\d{2})(?:/)?(\d{2})(?:/)?(\d{2})")
_ACTUAL_MARKERS = ("配息金額公告", "期後公告")
_ESTIMATED_MARKERS = ("配息期前公告", "期前公告", "預估", "估算")


@dataclass(frozen=True, slots=True)
class FirstDividendCandidate:
    etf_code: str
    fund_name: str
    document_id: str
    title: str
    document_url: str
    declared_date: date | None
    content_type: str = "application/pdf"
    information_basis: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class FirstDividendRejection:
    title: str
    reason: str


@dataclass(frozen=True, slots=True)
class FirstDividendDiscoveryResult:
    etf_code: str
    fund_name: str
    candidates: tuple[FirstDividendCandidate, ...]
    rejections: tuple[FirstDividendRejection, ...]


def _normalize_fund_name(value: str) -> str:
    normalized = re.sub(r"\s+", "", html.unescape(value))
    normalized = normalized.replace("證券投資信託", "")
    normalized = re.split(r"[（(](?:本基金|基金)", normalized, maxsplit=1)[0]
    return normalized.replace("臺", "台")


def parse_first_fund_name(*, etf_code: str, html_text: str) -> str:
    """從官方內嵌基金資料解析 ETF 證券代號與完整基金名稱。"""

    normalized_code = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized_code):
        raise ValueError("ETF 代號格式錯誤")
    decoded = html.unescape(html.unescape(html_text))
    for fund_name, stock_code in _FUND_PAIR_PATTERN.findall(decoded):
        if stock_code.upper() == normalized_code:
            return fund_name.strip()
    raise ValueError(f"第一金官方基金資料找不到 ETF：{normalized_code}")


class _NoticeParser(HTMLParser):
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
            self.links.append((self._href, re.sub(r"\s+", " ", " ".join(self._text)).strip()))
            self._href = None
            self._text = []


def parse_first_dividend_notices(
    *, etf_code: str, fund_name: str, html_text: str,
    max_documents: int = MAX_DOCUMENTS,
) -> FirstDividendDiscoveryResult:
    """依官方基金名稱篩選實際配息公告，拒絕期前與預估文件。"""

    normalized_code = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized_code):
        raise ValueError("ETF 代號格式錯誤")
    if max_documents < 1 or max_documents > MAX_DOCUMENTS:
        raise ValueError(f"max_documents 必須介於 1 與 {MAX_DOCUMENTS}")
    wanted_name = _normalize_fund_name(fund_name)
    parser = _NoticeParser()
    parser.feed(html_text)
    candidates: list[FirstDividendCandidate] = []
    rejections: list[FirstDividendRejection] = []
    seen: set[str] = set()
    source = get_actual_dividend_source(SOURCE_ID)
    for href, title in parser.links:
        searchable = _normalize_fund_name(f"{title} {href}")
        if wanted_name not in searchable and normalized_code not in searchable.upper():
            continue
        if any(marker in title for marker in _ESTIMATED_MARKERS):
            rejections.append(FirstDividendRejection(title, "公告屬於期前或預估資料"))
            continue
        if not any(marker in title or marker in href for marker in _ACTUAL_MARKERS):
            continue
        url = urljoin(NOTICE_URL, href.strip())
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in source.official_domains
            or not parsed.path.lower().endswith(".pdf")
        ):
            rejections.append(FirstDividendRejection(title, "公告不是第一金官方 PDF"))
            continue
        if url in seen:
            continue
        seen.add(url)
        match = _DATE_PATTERN.search(url)
        declared_date = date(*(int(value) for value in match.groups())) if match else None
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        candidates.append(FirstDividendCandidate(
            etf_code=normalized_code,
            fund_name=fund_name,
            document_id=f"first-dividend-{normalized_code}-{digest}",
            title=title,
            document_url=url,
            declared_date=declared_date,
        ))
        if len(candidates) >= max_documents:
            break
    return FirstDividendDiscoveryResult(
        normalized_code, fund_name, tuple(candidates), tuple(rejections),
    )


def _get(url: str, *, source) -> httpx.Response:
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
        raise ValueError("第一金官方回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("第一金官方來源未回傳 HTML")
    return response


def discover_first_dividend_documents(
    *, etf_code: str, allow_network: bool = False,
    max_documents: int = MAX_DOCUMENTS,
) -> FirstDividendDiscoveryResult:
    """依 ETF 代號自動探索第一金官方實際配息 PDF。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    source = get_actual_dividend_source(SOURCE_ID)
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    fund_data = _get(FUND_DATA_URL, source=source)
    notices = _get(NOTICE_URL, source=source)
    fund_name = parse_first_fund_name(etf_code=etf_code, html_text=fund_data.text)
    return parse_first_dividend_notices(
        etf_code=etf_code,
        fund_name=fund_name,
        html_text=notices.text,
        max_documents=max_documents,
    )
