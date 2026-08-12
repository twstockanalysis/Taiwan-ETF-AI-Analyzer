"""凱基投信 ETF 收益分配期後公告自動發現。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "kgi_etf_dividend_announcement"
DISCOVERY_URL = "https://www.kgifund.com.tw/Home/ArticleVC"
DOCUMENT_BASE_URL = "https://www.kgifund.com.tw/"
FUNCTION_ID = "1708"
MAX_RESPONSE_BYTES = 2_000_000
MAX_DOCUMENTS = 100
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_DATE_PATTERN = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


@dataclass(frozen=True, slots=True)
class KgiAnnouncementCandidate:
    """凱基官方收益分配期後 PDF 候選。"""

    etf_code: str
    source_id: str
    document_id: str
    title: str
    declared_date: date
    document_url: str
    content_type: str = "application/pdf"
    information_basis: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class KgiAnnouncementRejection:
    """凱基公告未進入期後 PDF 解析的原因。"""

    title: str
    reason: str


@dataclass(frozen=True, slots=True)
class KgiAnnouncementDiscoveryResult:
    """單一 ETF 的凱基公告發現結果。"""

    etf_code: str
    candidates: tuple[KgiAnnouncementCandidate, ...]
    rejections: tuple[KgiAnnouncementRejection, ...]


class _KgiAnnouncementParser(HTMLParser):
    """擷取 name=announcement 的官方連結與文字。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "a" and attributes.get("name") == "announcement":
            self._href = attributes.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            self.items.append((self._href, text))
            self._href = None
            self._text = []


def normalize_kgi_etf_code(etf_code: str) -> str:
    """正規化代號並阻擋路徑或表單注入。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    return normalized


def _official_document_url(href: str) -> str:
    source = get_actual_dividend_source(SOURCE_ID)
    raw_url = urljoin(DOCUMENT_BASE_URL, href.strip())
    parsed = urlsplit(raw_url)
    encoded_url = urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            quote(parsed.path, safe="/%._-()"),
            parsed.query,
            "",
        )
    )
    validate_official_source_url(source, encoded_url)
    return encoded_url


def parse_kgi_announcement_html(
    *, html_text: str, etf_code: str,
    max_documents: int = MAX_DOCUMENTS,
) -> KgiAnnouncementDiscoveryResult:
    """將官方 partial HTML 分成期後候選與拒絕項目。"""

    normalized_code = normalize_kgi_etf_code(etf_code)
    if max_documents < 1 or max_documents > MAX_DOCUMENTS:
        raise ValueError(f"max_documents 必須介於 1 與 {MAX_DOCUMENTS}")
    if not html_text.strip():
        raise ValueError("凱基公告回應為空白")

    parser = _KgiAnnouncementParser()
    parser.feed(html_text)
    candidates: list[KgiAnnouncementCandidate] = []
    rejections: list[KgiAnnouncementRejection] = []

    for href, text in parser.items[:max_documents]:
        title = _DATE_PATTERN.sub("", text, count=1).strip()
        if normalized_code not in title:
            rejections.append(KgiAnnouncementRejection(title, "公告不含目標 ETF 代號"))
            continue
        if "期前" in title or "預估" in title or "估算" in title:
            rejections.append(KgiAnnouncementRejection(title, "公告屬於期前或預估資料"))
            continue
        if "不予收益分配" in title:
            rejections.append(KgiAnnouncementRejection(title, "公告決定不予分配"))
            continue
        if "收益分配期後公告" not in title:
            rejections.append(KgiAnnouncementRejection(title, "公告不是收益分配期後公告"))
            continue
        if not href.lower().split("?", 1)[0].endswith(".pdf"):
            rejections.append(KgiAnnouncementRejection(title, "官方檔案不是 PDF"))
            continue

        date_match = _DATE_PATTERN.search(text)
        if date_match is None:
            rejections.append(KgiAnnouncementRejection(title, "公告缺少日期"))
            continue
        document_url = _official_document_url(href)
        digest = hashlib.sha256(document_url.encode("utf-8")).hexdigest()[:12]
        candidates.append(
            KgiAnnouncementCandidate(
                etf_code=normalized_code,
                source_id=SOURCE_ID,
                document_id=f"kgi-dividend-{normalized_code}-{digest}",
                title=title,
                declared_date=date.fromisoformat(date_match.group(1)),
                document_url=document_url,
            )
        )

    return KgiAnnouncementDiscoveryResult(
        etf_code=normalized_code,
        candidates=tuple(candidates),
        rejections=tuple(rejections),
    )


def fetch_kgi_announcement_html(
    *, etf_code: str, allow_network: bool = False,
    timeout_seconds: float = 30.0,
) -> str:
    """明確允許後查詢凱基 ETF 公告 partial HTML。"""

    normalized_code = normalize_kgi_etf_code(etf_code)
    source = get_actual_dividend_source(SOURCE_ID)
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")

    response = httpx.post(
        DISCOVERY_URL,
        data={"tags": "ETF", "keyword": normalized_code, "functionId": FUNCTION_ID},
        timeout=timeout_seconds,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={
            "Accept": "text/html",
            "User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)",
        },
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type:
        raise ValueError("凱基公告查詢回傳非 HTML 內容")
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("凱基公告回應超過容量上限")
    return response.text


def discover_kgi_actual_dividend_announcements(
    *, etf_code: str, allow_network: bool = False,
    html_text: str | None = None,
) -> KgiAnnouncementDiscoveryResult:
    """查詢並分流凱基收益分配公告。"""

    normalized_code = normalize_kgi_etf_code(etf_code)
    if html_text is None:
        html_text = fetch_kgi_announcement_html(
            etf_code=normalized_code,
            allow_network=allow_network,
        )
    return parse_kgi_announcement_html(
        html_text=html_text,
        etf_code=normalized_code,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="發現凱基 ETF 收益分配期後 PDF")
    parser.add_argument("--etf-code", required=True)
    parser.add_argument("--allow-network", action="store_true")
    arguments = parser.parse_args(argv)
    if not arguments.allow_network:
        raise ValueError("自動發現必須明確指定 --allow-network")
    result = discover_kgi_actual_dividend_announcements(
        etf_code=arguments.etf_code,
        allow_network=True,
    )
    print(json.dumps({
        "etf_code": result.etf_code,
        "candidates": [
            {
                "document_id": item.document_id,
                "title": item.title,
                "declared_date": item.declared_date.isoformat(),
                "document_url": item.document_url,
                "information_basis": item.information_basis,
            }
            for item in result.candidates
        ],
        "rejections": [
            {"title": item.title, "reason": item.reason}
            for item in result.rejections
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
