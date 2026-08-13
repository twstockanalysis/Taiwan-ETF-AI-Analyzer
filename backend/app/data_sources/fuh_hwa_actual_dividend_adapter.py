"""復華投信官方 ETF 歷史配息與組成文件 Adapter。"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from urllib.parse import urlsplit

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "fuh_hwa_etf_dividend_document"
HISTORY_URL = "https://www.fhtrust.com.tw/ETF/etf_history"
DETAIL_URL = "https://www.fhtrust.com.tw/ETF/etf_detail/ETF01"
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_MAPPING_PATTERN = re.compile(
    r'<option\s+value="(ETF\d+)">\s*([0-9A-Z]+)_', re.I,
)
_ROW_PATTERN = re.compile(
    r'<tr\s+class="fundListTable-fundCard"[^>]*>(.*?)</tr>', re.I | re.S,
)
_CELL_PATTERN = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
_TAG_PATTERN = re.compile(r"<[^>]+>")


@dataclass(frozen=True, slots=True)
class FuhHwaDividendAmount:
    etf_code: str
    fund_name: str
    amount_per_unit: Decimal
    distribution_rate_percent: Decimal | None
    period_return_percent: Decimal | None
    ex_dividend_date: date
    payment_date: date
    currency: str
    frequency: str
    composition_document_url: str
    information_basis: str = "ACTUAL_AMOUNT_ONLY"


def _plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_PATTERN.sub(" ", value))).strip()


def parse_fuh_hwa_internal_id(*, etf_code: str, html_text: str) -> str:
    """由官方 ETF 選單解析證券代號對應的 ETFxx 內部 ID。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    for internal_id, stock_code in _MAPPING_PATTERN.findall(html_text):
        if stock_code.upper() == normalized:
            return internal_id.upper()
    raise ValueError(f"復華官方 ETF 選單找不到證券代號：{normalized}")


def _optional_percent(value: str) -> Decimal | None:
    normalized = value.replace("%", "").strip()
    return None if normalized in {"", "—", "-"} else Decimal(normalized)


def _previous_month(value: date) -> str:
    year = value.year if value.month > 1 else value.year - 1
    month = value.month - 1 if value.month > 1 else 12
    return f"{year:04d}{month:02d}"


def parse_fuh_hwa_dividend_amounts(
    *, etf_code: str, internal_id: str, html_text: str,
) -> tuple[FuhHwaDividendAmount, ...]:
    """解析目標 ETF 歷史配息，並建立官方組成 PDF 候選網址。"""

    normalized = etf_code.strip().upper()
    rows: list[FuhHwaDividendAmount] = []
    for row_html in _ROW_PATTERN.findall(html_text):
        cells = [_plain_text(cell) for cell in _CELL_PATTERN.findall(row_html)]
        if len(cells) != 9 or cells[0].upper() != normalized:
            continue
        ex_date = date.fromisoformat(cells[5].replace("/", "-"))
        document_url = (
            "https://www.fhtrust.com.tw/docUpload/Distribution/"
            f"{_previous_month(ex_date)}/{internal_id.upper()}_A.pdf"
        )
        rows.append(FuhHwaDividendAmount(
            etf_code=normalized,
            fund_name=cells[1],
            amount_per_unit=Decimal(cells[2]),
            distribution_rate_percent=_optional_percent(cells[3]),
            period_return_percent=_optional_percent(cells[4]),
            ex_dividend_date=ex_date,
            payment_date=date.fromisoformat(cells[6].replace("/", "-")),
            currency=cells[7],
            frequency=cells[8],
            composition_document_url=document_url,
        ))
    return tuple(rows)


def _validate_html(response: httpx.Response, *, source) -> None:
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("復華投信官方回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("復華投信官方來源未回傳 HTML")


def fetch_fuh_hwa_dividend_amounts(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[FuhHwaDividendAmount, ...]:
    """取得復華官方歷史配息，並保留已驗證格式的組成文件網址。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    source = get_actual_dividend_source(SOURCE_ID)
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    client = httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    detail = client.get(DETAIL_URL)
    history = client.get(HISTORY_URL)
    _validate_html(detail, source=source)
    _validate_html(history, source=source)
    internal_id = parse_fuh_hwa_internal_id(
        etf_code=etf_code, html_text=detail.text,
    )
    rows = parse_fuh_hwa_dividend_amounts(
        etf_code=etf_code, internal_id=internal_id, html_text=history.text,
    )
    if rows:
        latest_url = rows[0].composition_document_url
        response = client.get(latest_url)
        if response.status_code == 200:
            validate_official_source_url(source, str(response.url))
            if (
                len(response.content) > MAX_RESPONSE_BYTES
                or "application/pdf" not in response.headers.get("content-type", "").lower()
                or urlsplit(str(response.url)).scheme != "https"
            ):
                raise ValueError("復華最新組成文件不是有效的官方 PDF")
    return rows
