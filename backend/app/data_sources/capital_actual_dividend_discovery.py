"""群益投信 ETF 收益分配期後公告自動發現。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "capital_etf_dividend_document"
FUND_INFO_URL = "https://www.capitalfund.com.tw/CFWeb/api/etf/DividendInfo"
ANNOUNCEMENT_LIST_URL = (
    "https://www.capitalfund.com.tw/etf/product/news/list/2"
)
BASE_URL = "https://www.capitalfund.com.tw/"
MAX_RESPONSE_BYTES = 2_000_000
MAX_ARTICLES = 10
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_DATE_PATTERN = re.compile(r"(20\d{2})/(\d{2})/(\d{2})")


@dataclass(frozen=True, slots=True)
class CapitalAnnouncementCandidate:
    etf_code: str
    source_id: str
    document_id: str
    title: str
    declared_date: date
    document_url: str
    content_type: str = "application/pdf"
    information_basis: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class CapitalAnnouncementRejection:
    title: str
    reason: str


@dataclass(frozen=True, slots=True)
class CapitalAnnouncementReference:
    title: str
    declared_date: date
    article_url: str


@dataclass(frozen=True, slots=True)
class CapitalAnnouncementDiscoveryResult:
    etf_code: str
    candidates: tuple[CapitalAnnouncementCandidate, ...]
    rejections: tuple[CapitalAnnouncementRejection, ...]
    latest_page_only: bool = True


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._href = dict(attrs).get("href")
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            self.links.append((self._href, text))
            self._href = None
            self._text = []


def normalize_capital_etf_code(etf_code: str) -> str:
    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    return normalized


def resolve_capital_short_name(payload: dict, etf_code: str) -> str:
    """從群益官方 DividendInfo 回應取得 ETF 簡稱。"""

    normalized = normalize_capital_etf_code(etf_code)
    if payload.get("code") != 200 or not isinstance(payload.get("data"), list):
        raise ValueError("群益 ETF 清單回應格式錯誤")
    for item in payload["data"]:
        if str(item.get("stockNo", "")).strip().upper() == normalized:
            short_name = str(item.get("shortName", "")).strip()
            if not short_name:
                raise ValueError("群益 ETF 清單缺少基金簡稱")
            return short_name
    raise ValueError(f"群益官方清單找不到 ETF：{normalized}")


def parse_capital_announcement_list(
    *, html_text: str, short_name: str,
) -> tuple[tuple[CapitalAnnouncementReference, ...], tuple[CapitalAnnouncementRejection, ...]]:
    """只接受最新公告页中目标基金的期后公告。"""

    if not html_text.strip() or not short_name.strip():
        raise ValueError("群益公告或基金簡稱不可空白")
    parser = _LinkParser()
    parser.feed(html_text)
    references: list[CapitalAnnouncementReference] = []
    rejections: list[CapitalAnnouncementRejection] = []
    seen: set[str] = set()
    for href, text in parser.links:
        if not re.fullmatch(r"/etf/product/news/\d+", href) or href in seen:
            continue
        seen.add(href)
        title = text.strip()
        if short_name not in title:
            continue
        if "期前公告" in title or "預估" in title:
            rejections.append(CapitalAnnouncementRejection(title, "公告屬於期前或預估資料"))
            continue
        if "期後公告" not in title or "實際配發金額" not in title:
            rejections.append(CapitalAnnouncementRejection(title, "公告不是收益分配期後實際配發公告"))
            continue
        match = _DATE_PATTERN.search(title)
        if match is None:
            rejections.append(CapitalAnnouncementRejection(title, "公告缺少西元日期"))
            continue
        references.append(CapitalAnnouncementReference(
            title=title,
            declared_date=date(*(int(value) for value in match.groups())),
            article_url=urljoin(BASE_URL, href),
        ))
        if len(references) >= MAX_ARTICLES:
            break
    return tuple(references), tuple(rejections)


def parse_capital_article_pdf_url(html_text: str) -> str:
    """從群益期後文章取得官方 PDF 附件。"""

    parser = _LinkParser()
    parser.feed(html_text)
    source = get_actual_dividend_source(SOURCE_ID)
    for href, _ in parser.links:
        url = urljoin(BASE_URL, href.strip())
        if "/ECStorge/fund/news/" in url and url.lower().endswith(".pdf"):
            validate_official_source_url(source, url)
            return url
    raise ValueError("群益期後公告找不到官方 PDF 附件")


def build_capital_candidates(
    *, etf_code: str, references: tuple[CapitalAnnouncementReference, ...],
    article_html_by_url: dict[str, str],
) -> tuple[CapitalAnnouncementCandidate, ...]:
    normalized = normalize_capital_etf_code(etf_code)
    candidates: list[CapitalAnnouncementCandidate] = []
    for reference in references:
        pdf_url = parse_capital_article_pdf_url(
            article_html_by_url[reference.article_url]
        )
        digest = hashlib.sha256(pdf_url.encode("utf-8")).hexdigest()[:12]
        candidates.append(CapitalAnnouncementCandidate(
            etf_code=normalized,
            source_id=SOURCE_ID,
            document_id=f"capital-dividend-{normalized}-{digest}",
            title=reference.title,
            declared_date=reference.declared_date,
            document_url=pdf_url,
        ))
    return tuple(candidates)


def _request(*, url: str, method: str, allow_network: bool) -> httpx.Response:
    source = get_actual_dividend_source(SOURCE_ID)
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.request(
        method, url, timeout=30.0, follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("群益官方回應超過容量上限")
    return response


def discover_capital_actual_dividend_announcements(
    *, etf_code: str, allow_network: bool = False,
) -> CapitalAnnouncementDiscoveryResult:
    """从官方清单、最新公告页及文章附件发现期后 PDF。"""

    normalized = normalize_capital_etf_code(etf_code)
    info = _request(url=FUND_INFO_URL, method="POST", allow_network=allow_network)
    short_name = resolve_capital_short_name(info.json(), normalized)
    listing = _request(
        url=ANNOUNCEMENT_LIST_URL, method="GET", allow_network=allow_network
    )
    references, rejections = parse_capital_announcement_list(
        html_text=listing.text, short_name=short_name
    )
    article_html = {
        item.article_url: _request(
            url=item.article_url, method="GET", allow_network=allow_network
        ).text
        for item in references
    }
    return CapitalAnnouncementDiscoveryResult(
        etf_code=normalized,
        candidates=build_capital_candidates(
            etf_code=normalized,
            references=references,
            article_html_by_url=article_html,
        ),
        rejections=rejections,
    )
