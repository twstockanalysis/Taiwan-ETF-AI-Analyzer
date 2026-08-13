"""聯邦投信官方 ETF 配息紀錄 HTML Adapter。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
import re

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "union_etf_dividend_document"
DIVIDEND_URL = "https://www.usitc.com.tw/Fund/FundDividend_ETF"
MAX_RESPONSE_BYTES = 2_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_FUND_BY_ETF_CODE = {"009804": "00572518"}


@dataclass(frozen=True, slots=True)
class UnionDividendAmount:
    etf_code: str
    frequency: str
    ex_dividend_date: date
    amount_per_unit: Decimal
    reference_nav: Decimal
    distribution_rate_percent: Decimal
    total_return_percent: Decimal | None
    information_basis: str = "ACTUAL_AMOUNT_ONLY"


class _DividendTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, str]] = []
        self._row: dict[str, str] | None = None
        self._field: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag == "tr":
            self._row = {}
        elif tag == "td" and self._row is not None:
            self._field = attributes.get("data-title")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._field is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._row is not None and self._field is not None:
            self._row[self._field] = " ".join(self._text).strip()
            self._field = None
            self._text = []
        elif tag == "tr" and self._row is not None:
            if "每單位配息金額" in self._row:
                self.rows.append(self._row)
            self._row = None


def parse_union_dividend_amounts(
    *, etf_code: str, html: str,
) -> tuple[UnionDividendAmount, ...]:
    """解析官方 ETF 配息表，不推論未揭露的所得組成。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    if normalized not in _FUND_BY_ETF_CODE:
        raise ValueError("聯邦 ETF 代號尚未建立官方基金編號對照")
    parser = _DividendTableParser()
    parser.feed(html)
    rows: list[UnionDividendAmount] = []
    frequency = ""
    for item in parser.rows:
        frequency = item.get("級別", "").strip() or frequency
        total_return = item.get("當期報酬率(含息)", "").strip()
        rows.append(UnionDividendAmount(
            etf_code=normalized,
            frequency=frequency,
            ex_dividend_date=date.fromisoformat(
                item["除息日"].replace("/", "-")
            ),
            amount_per_unit=Decimal(item["每單位配息金額"]),
            reference_nav=Decimal(item["配息基準日淨值"]),
            distribution_rate_percent=Decimal(item["當期配息率(%)"]),
            total_return_percent=(
                None if not total_return or total_return == "-"
                else Decimal(total_return)
            ),
        ))
    return tuple(rows)


def fetch_union_dividend_amounts(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[UnionDividendAmount, ...]:
    """依已驗證的 ETF 與基金編號對照查詢聯邦官方配息表。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    normalized = etf_code.strip().upper()
    if normalized not in _FUND_BY_ETF_CODE:
        raise ValueError("聯邦 ETF 代號尚未建立官方基金編號對照")
    source = get_actual_dividend_source(SOURCE_ID)
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.get(
        DIVIDEND_URL,
        params={"FundType": 7, "FundNo": _FUND_BY_ETF_CODE[normalized]},
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("聯邦官方 ETF 配息頁超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("聯邦官方 ETF 配息頁未回傳 HTML")
    return parse_union_dividend_amounts(etf_code=normalized, html=response.text)
