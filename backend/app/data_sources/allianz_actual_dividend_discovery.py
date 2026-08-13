"""安聯投信官方產品公告的 ETF 配息文件發現器。"""

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
_DATE_PATTERN = re.compile(r"(20\d{2})[/-](\d{1,2})[/-](\d{1,2})")
_ACTUAL_WORDS = ("實際配發", "期後收益分配", "收益分配期後")
_ESTIMATED_WORDS = ("期前", "預估", "估算")


@dataclass(frozen=True, slots=True)
class AllianzDividendCandidate:
    etf_code: str
    document_id: str
    title: str
    document_url: str
    declared_date: date | None
    content_type: str
    information_basis: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class AllianzDividendRejection:
    title: str
    reason: str


@dataclass(frozen=True, slots=True)
class AllianzDividendDiscoveryResult:
    etf_code: str
    candidates: tuple[AllianzDividendCandidate, ...]
    rejections: tuple[AllianzDividendRejection, ...]


class _ArticleTileParser(HTMLParser):
    """擷取公告卡片；安聯卡片的可見連結文字通常只有「了解更多」。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tiles: list[tuple[str, str]] = []
        self._tile_depth = 0
        self._href: str | None = None
        self._label = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "div":
            classes = (attributes.get("class") or "").split()
            if self._tile_depth:
                self._tile_depth += 1
            elif "tile-article" in classes:
                self._tile_depth = 1
                self._href = None
                self._label = ""
                self._text = []
        if self._tile_depth and tag.lower() == "a" and self._href is None:
            self._href = attributes.get("href")
            self._label = (
                attributes.get("aria-label")
                or attributes.get("title")
                or ""
            )

    def handle_data(self, data: str) -> None:
        if self._tile_depth:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "div" or not self._tile_depth:
            return
        self._tile_depth -= 1
        if self._tile_depth == 0 and self._href:
            text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            label = re.sub(r"\s+", " ", self._label).strip()
            self.tiles.append((self._href, label or text))


def parse_allianz_product_announcements(
    *, etf_code: str, html_text: str, max_documents: int = MAX_DOCUMENTS,
) -> AllianzDividendDiscoveryResult:
    """解析官方產品公告，只留下目標 ETF 的實際／期後配息公告。"""

    page = get_issuer_dividend_landing_page("allianz")
    normalized_code = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized_code):
        raise ValueError("ETF 代號格式錯誤")
    if max_documents < 1 or max_documents > MAX_DOCUMENTS:
        raise ValueError(f"max_documents 必須介於 1 與 {MAX_DOCUMENTS}")
    if not html_text.strip():
        raise ValueError("安聯官方產品公告回應為空白")

    parser = _ArticleTileParser()
    parser.feed(html_text)
    candidates: list[AllianzDividendCandidate] = []
    rejections: list[AllianzDividendRejection] = []
    seen: set[str] = set()
    for href, title in parser.tiles:
        searchable = f"{title} {href}".upper()
        if normalized_code not in searchable:
            continue
        if any(word in title for word in _ESTIMATED_WORDS):
            rejections.append(AllianzDividendRejection(
                title, "公告屬於期前或預估資料",
            ))
            continue
        if not any(word in title for word in _ACTUAL_WORDS):
            continue
        url = urljoin(page.url, href.strip())
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in page.official_domains:
            rejections.append(AllianzDividendRejection(
                title, "公告連結不在安聯投信官方網域",
            ))
            continue
        if url in seen:
            continue
        seen.add(url)
        match = _DATE_PATTERN.search(title)
        declared_date = (
            date(*(int(value) for value in match.groups()))
            if match is not None else None
        )
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        candidates.append(AllianzDividendCandidate(
            etf_code=normalized_code,
            document_id=f"allianz-dividend-{normalized_code}-{digest}",
            title=title,
            document_url=url,
            declared_date=declared_date,
            content_type=(
                "application/pdf" if parsed.path.lower().endswith(".pdf")
                else "text/html"
            ),
        ))
        if len(candidates) >= max_documents:
            break
    return AllianzDividendDiscoveryResult(
        normalized_code, tuple(candidates), tuple(rejections),
    )


def discover_allianz_dividend_documents(
    *, etf_code: str, allow_network: bool = False,
    max_documents: int = MAX_DOCUMENTS,
) -> AllianzDividendDiscoveryResult:
    """明確授權後下載安聯官方產品公告頁並探索正式配息文件。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    page = get_issuer_dividend_landing_page("allianz")
    response = httpx.get(
        page.url,
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "Mozilla/5.0 TW-ETF-AI-Analyzer/0.1"},
    )
    response.raise_for_status()
    final_url = urlsplit(str(response.url))
    if final_url.scheme != "https" or final_url.hostname not in page.official_domains:
        raise ValueError("安聯官方產品公告重新導向至非官方網域")
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("安聯官方產品公告回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("安聯官方產品公告未回傳 HTML")
    return parse_allianz_product_announcements(
        etf_code=etf_code,
        html_text=response.text,
        max_documents=max_documents,
    )
