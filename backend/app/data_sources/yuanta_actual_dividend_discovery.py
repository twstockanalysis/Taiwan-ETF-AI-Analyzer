"""元大投信官方 ETF 公告的配息文件發現器。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx

from backend.app.data_sources.issuer_dividend_landing_pages import (
    get_issuer_dividend_landing_page,
)
from backend.app.data_sources.openapi import create_ssl_context


MAX_DOCUMENTS = 50
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_DATE_PATTERN = re.compile(r"(20\d{2})/(\d{1,2})/(\d{1,2})")
_ACTUAL_WORDS = ("實際配發金額", "每受益權單位實際配發")
_ESTIMATED_WORDS = ("預估", "期前", "評價結果")
_FUND_NAME_ALIASES = {
    "00940": ("元大臺灣價值高息ETF", "元大台灣價值高息ETF"),
}


@dataclass(frozen=True, slots=True)
class YuantaDividendCandidate:
    etf_code: str
    document_id: str
    title: str
    document_url: str
    declared_date: date | None
    information_basis: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class YuantaDividendRejection:
    title: str
    reason: str


@dataclass(frozen=True, slots=True)
class YuantaDividendDiscoveryResult:
    etf_code: str
    candidates: tuple[YuantaDividendCandidate, ...]
    rejections: tuple[YuantaDividendRejection, ...]


class _AnnouncementParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        href = dict(attrs).get("href")
        if tag == "a" and href and href.startswith("/news/announcement/"):
            self._href = href
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            title = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            self.links.append((self._href, title))
            self._href = None
            self._text = []


def parse_yuanta_announcements(
    *, etf_code: str, html_text: str, max_documents: int = MAX_DOCUMENTS,
) -> YuantaDividendDiscoveryResult:
    """只接受目標 ETF 明示實際配發金額的官方公告。"""

    page = get_issuer_dividend_landing_page("yuanta")
    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    if max_documents < 1 or max_documents > MAX_DOCUMENTS:
        raise ValueError(f"max_documents 必須介於 1 與 {MAX_DOCUMENTS}")
    if not html_text.strip():
        raise ValueError("元大官方公告回應為空白")
    parser = _AnnouncementParser()
    parser.feed(html_text)
    candidates: list[YuantaDividendCandidate] = []
    rejections: list[YuantaDividendRejection] = []
    seen: set[str] = set()
    for href, title in parser.links:
        aliases = _FUND_NAME_ALIASES.get(normalized, ())
        if normalized not in title.upper() and not any(
            alias in title for alias in aliases
        ):
            continue
        if any(word in title for word in _ESTIMATED_WORDS):
            rejections.append(YuantaDividendRejection(
                title, "公告屬於評價、期前或預估資料",
            ))
            continue
        if not any(word in title for word in _ACTUAL_WORDS):
            continue
        url = urljoin(page.url, href)
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in page.official_domains:
            rejections.append(YuantaDividendRejection(
                title, "公告連結不在元大投信官方網域",
            ))
            continue
        if url in seen:
            continue
        seen.add(url)
        match = _DATE_PATTERN.search(title)
        candidates.append(YuantaDividendCandidate(
            etf_code=normalized,
            document_id=(f"yuanta-dividend-{normalized}-"
                         f"{hashlib.sha256(url.encode()).hexdigest()[:12]}"),
            title=title,
            document_url=url,
            declared_date=(date(*(int(v) for v in match.groups())) if match else None),
        ))
        if len(candidates) >= max_documents:
            break
    return YuantaDividendDiscoveryResult(
        normalized, tuple(candidates), tuple(rejections),
    )


def discover_yuanta_dividend_documents(
    *, etf_code: str, allow_network: bool = False,
    max_documents: int = MAX_DOCUMENTS,
) -> YuantaDividendDiscoveryResult:
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    page = get_issuer_dividend_landing_page("yuanta")
    response = httpx.get(
        page.url, timeout=30.0, follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "Mozilla/5.0 TW-ETF-AI-Analyzer/0.1"},
    )
    response.raise_for_status()
    final_url = urlsplit(str(response.url))
    if final_url.scheme != "https" or final_url.hostname not in page.official_domains:
        raise ValueError("元大官方公告重新導向至非官方網域")
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("元大官方公告回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("元大官方公告未回傳 HTML")
    return parse_yuanta_announcements(
        etf_code=etf_code, html_text=response.text,
        max_documents=max_documents,
    )
