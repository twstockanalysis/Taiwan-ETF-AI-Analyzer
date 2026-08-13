"""投信官方公告入口的共用 ETF 配息文件發現器。"""

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
_DIVIDEND_WORDS = ("收益分配", "配息公告", "實際配發")
_ESTIMATED_WORDS = ("期前", "預估", "估算")
_ONCLICK_HTTPS_URL_PATTERN = re.compile(r"https://[^'\"\s)]+")


@dataclass(frozen=True, slots=True)
class IssuerLandingPageCandidate:
    issuer_key: str
    etf_code: str
    document_id: str
    title: str
    document_url: str
    declared_date: date | None
    content_type: str
    information_basis: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class IssuerLandingPageRejection:
    title: str
    reason: str


@dataclass(frozen=True, slots=True)
class IssuerLandingPageDiscoveryResult:
    issuer_key: str
    etf_code: str
    candidates: tuple[IssuerLandingPageCandidate, ...]
    rejections: tuple[IssuerLandingPageRejection, ...]


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            attributes = dict(attrs)
            href = attributes.get("href")
            onclick = attributes.get("onclick") or ""
            onclick_url = _ONCLICK_HTTPS_URL_PATTERN.search(onclick)
            self._href = onclick_url.group(0) if onclick_url is not None else href
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


def parse_issuer_landing_page(
    *, issuer_key: str, etf_code: str, html_text: str,
    max_documents: int = MAX_DOCUMENTS,
) -> IssuerLandingPageDiscoveryResult:
    """從已驗證的投信官方入口擷取目標 ETF 配息連結。"""

    page = get_issuer_dividend_landing_page(issuer_key)
    normalized_code = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized_code):
        raise ValueError("ETF 代號格式錯誤")
    if max_documents < 1 or max_documents > MAX_DOCUMENTS:
        raise ValueError(f"max_documents 必須介於 1 與 {MAX_DOCUMENTS}")
    if not html_text.strip():
        raise ValueError("投信官方公告入口回應為空白")

    parser = _AnchorParser()
    parser.feed(html_text)
    candidates: list[IssuerLandingPageCandidate] = []
    rejections: list[IssuerLandingPageRejection] = []
    seen: set[str] = set()
    for href, title in parser.links:
        searchable = f"{title} {href}".upper()
        if normalized_code not in searchable:
            continue
        if not any(word in title for word in _DIVIDEND_WORDS):
            continue
        if any(word in title for word in _ESTIMATED_WORDS):
            rejections.append(
                IssuerLandingPageRejection(title, "公告屬於期前或預估資料")
            )
            continue
        url = urljoin(page.url, href.strip())
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in page.official_domains:
            rejections.append(
                IssuerLandingPageRejection(title, "公告連結不在投信官方網域")
            )
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
        candidates.append(IssuerLandingPageCandidate(
            issuer_key=page.issuer_key,
            etf_code=normalized_code,
            document_id=f"{page.issuer_key}-dividend-{normalized_code}-{digest}",
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
    return IssuerLandingPageDiscoveryResult(
        page.issuer_key, normalized_code, tuple(candidates), tuple(rejections)
    )


def discover_issuer_landing_page_documents(
    *, issuer_key: str, etf_code: str, allow_network: bool = False,
    max_documents: int = MAX_DOCUMENTS,
) -> IssuerLandingPageDiscoveryResult:
    """下載投信官方入口，並以保守規則發現配息公告候選文件。"""

    page = get_issuer_dividend_landing_page(issuer_key)
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if page.network_access != "DIRECT":
        raise ValueError(f"投信官方入口不允許直接程式查詢：{page.issuer_key}")
    response = httpx.get(
        page.url,
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    final_url = urlsplit(str(response.url))
    if final_url.scheme != "https" or final_url.hostname not in page.official_domains:
        raise ValueError("投信官方入口重新導向至非官方網域")
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("投信官方入口回應超過容量上限")
    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type:
        raise ValueError("投信官方入口未回傳 HTML")
    return parse_issuer_landing_page(
        issuer_key=page.issuer_key,
        etf_code=etf_code,
        html_text=response.text,
        max_documents=max_documents,
    )
