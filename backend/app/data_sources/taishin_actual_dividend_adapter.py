"""台新投信官方 ETF 歷史配息組成表 Adapter。"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "taishin_etf_dividend_document"
DIVIDEND_URL = "https://www.tsit.com.tw/ETF/Home/ETFDIVList"
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_ROW_PATTERN = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
_CELL_PATTERN = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
_TAG_PATTERN = re.compile(r"<[^>]+>")
_DATE_PATTERN = re.compile(r"(20\d{2})/(\d{1,2})/(\d{1,2})")


@dataclass(frozen=True, slots=True)
class TaishinDividendComposition:
    etf_code: str
    distribution_month: str
    frequency: str
    evaluation_date: date
    ex_dividend_date: date
    payment_date: date
    amount_per_unit: Decimal
    dividend_yield_percent: Decimal
    dividend_interest_percent: Decimal
    capital_gain_percent: Decimal
    other_income_percent: Decimal
    income_equalization_percent: Decimal
    information_basis: str = "ACTUAL"


def _plain_text(value: str) -> str:
    return re.sub(
        r"\s+", " ", html.unescape(_TAG_PATTERN.sub(" ", value))
    ).strip()


def _parse_date(value: str) -> date:
    match = _DATE_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"台新配息日期格式錯誤：{value}")
    return date(*(int(part) for part in match.groups()))


def parse_taishin_dividend_compositions(
    *, etf_code: str, html_text: str,
) -> tuple[TaishinDividendComposition, ...]:
    """解析目標 ETF 的官方歷史配息金額與四類組成比例。"""

    normalized_code = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized_code):
        raise ValueError("ETF 代號格式錯誤")
    marker = re.search(
        rf'class="card-header[^\"]*"[^>]*id="{re.escape(normalized_code)}"',
        html_text,
        re.I,
    )
    if marker is None:
        raise ValueError(f"台新官方配息表找不到 ETF：{normalized_code}")
    next_card = html_text.find('class="card-header', marker.end())
    section = html_text[marker.end():next_card if next_card >= 0 else None]
    rows: list[TaishinDividendComposition] = []
    for row_html in _ROW_PATTERN.findall(section):
        cells = [_plain_text(cell) for cell in _CELL_PATTERN.findall(row_html)]
        if len(cells) != 10:
            continue
        event_dates = _DATE_PATTERN.findall(cells[2])
        if len(event_dates) != 2:
            raise ValueError("台新配息列缺少評價日或除息日")
        percentages = tuple(Decimal(value) for value in cells[5:9])
        if abs(sum(percentages) - Decimal("100")) > Decimal("0.02"):
            raise ValueError("台新配息組成比例合計不等於 100%")
        rows.append(TaishinDividendComposition(
            etf_code=normalized_code,
            distribution_month=re.sub(r"\s+", "", cells[0]),
            frequency=cells[1],
            evaluation_date=date(*(int(v) for v in event_dates[0])),
            ex_dividend_date=date(*(int(v) for v in event_dates[1])),
            amount_per_unit=Decimal(cells[3]),
            dividend_yield_percent=Decimal(cells[4]),
            dividend_interest_percent=percentages[0],
            capital_gain_percent=percentages[1],
            other_income_percent=percentages[2],
            income_equalization_percent=percentages[3],
            payment_date=_parse_date(cells[9]),
        ))
    if not rows:
        raise ValueError(f"台新官方配息表沒有 ETF 資料列：{normalized_code}")
    return tuple(rows)


def fetch_taishin_dividend_compositions(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[TaishinDividendComposition, ...]:
    """下載並解析台新官方歷史配息組成表。"""

    source = get_actual_dividend_source(SOURCE_ID)
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.get(
        DIVIDEND_URL,
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("台新官方配息表回應超過容量上限")
    return parse_taishin_dividend_compositions(
        etf_code=etf_code,
        html_text=response.text,
    )
