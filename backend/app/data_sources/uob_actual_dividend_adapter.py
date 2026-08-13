"""大華銀投信官方 ETF 歷史配息金額 Adapter。"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
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


SOURCE_ID = "uob_etf_dividend_document"
BASE_URL = "https://www.uobam.com.tw/"
DIVIDEND_URL = "https://www.uobam.com.tw/dividend?type=etf"
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_FUND_URL_PATTERN = re.compile(r'href="([^"]*/fund/etf/(\d+)(?:#[^"]*)?)"', re.I)
_H1_PATTERN = re.compile(r"<h1>(.*?)</h1>", re.I | re.S)
_ROW_PATTERN = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
_CELL_PATTERN = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
_TAG_PATTERN = re.compile(r"<[^>]+>")


@dataclass(frozen=True, slots=True)
class UOBDividendAmount:
    etf_code: str
    currency: str
    amount_per_unit: Decimal
    evaluation_date: date
    ex_dividend_date: date
    payment_date: date
    frequency: str
    information_basis: str = "ACTUAL_AMOUNT_ONLY"


def _plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_PATTERN.sub(" ", value))).strip()


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.strip().replace("/", "-"))


def parse_uob_fund_detail_url(*, etf_code: str, html_text: str) -> str:
    """從官方 ETF 活動頁取得數字基金 ID 詳細頁。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    for href, _ in _FUND_URL_PATTERN.findall(html_text):
        url = urljoin(BASE_URL, href).split("#", 1)[0]
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname == "www.uobam.com.tw":
            return url
    raise ValueError(f"大華銀官方活動頁找不到 ETF 基金 ID：{normalized}")


def parse_uob_fund_name(html_text: str) -> str:
    match = _H1_PATTERN.search(html_text)
    if match is None:
        raise ValueError("大華銀官方基金頁找不到基金名稱")
    name = _plain_text(match.group(1))
    if not name:
        raise ValueError("大華銀官方基金名稱為空白")
    return name


def parse_uob_dividend_amounts(
    *, etf_code: str, fund_name: str, html_text: str,
) -> tuple[UOBDividendAmount, ...]:
    """以已驗證基金名稱解析官方歷史配息金額與日期。"""

    normalized = etf_code.strip().upper()
    marker = html_text.find(f'<div class="name">{fund_name}</div>')
    if marker < 0:
        raise ValueError(f"大華銀配息頁找不到基金：{normalized}")
    next_item = html_text.find('<div class="item">', marker + 1)
    section = html_text[marker:next_item if next_item >= 0 else None]
    rows: list[UOBDividendAmount] = []
    for row_html in _ROW_PATTERN.findall(section):
        cells = [_plain_text(cell) for cell in _CELL_PATTERN.findall(row_html)]
        if len(cells) != 6:
            continue
        rows.append(UOBDividendAmount(
            etf_code=normalized,
            currency=cells[0],
            amount_per_unit=Decimal(cells[1]),
            evaluation_date=_parse_date(cells[2]),
            ex_dividend_date=_parse_date(cells[3]),
            payment_date=_parse_date(cells[4]),
            frequency=cells[5],
        ))
    if not rows:
        raise ValueError(f"大華銀配息頁沒有基金資料列：{normalized}")
    return tuple(rows)


def _get(url: str, *, source, allow_network: bool) -> httpx.Response:
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.get(
        url, timeout=30.0, follow_redirects=True, verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("大華銀官方回應超過容量上限")
    return response


def fetch_uob_dividend_amounts(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[UOBDividendAmount, ...]:
    """自動解析 ETF 代號、基金 ID、名稱與官方歷史配息金額。"""

    normalized = etf_code.strip().upper()
    source = get_actual_dividend_source(SOURCE_ID)
    event = _get(
        urljoin(BASE_URL, f"Events/{normalized}ETF/"),
        source=source,
        allow_network=allow_network,
    )
    detail_url = parse_uob_fund_detail_url(
        etf_code=normalized, html_text=event.text
    )
    detail = _get(detail_url, source=source, allow_network=allow_network)
    listing = _get(DIVIDEND_URL, source=source, allow_network=allow_network)
    return parse_uob_dividend_amounts(
        etf_code=normalized,
        fund_name=parse_uob_fund_name(detail.text),
        html_text=listing.text,
    )
