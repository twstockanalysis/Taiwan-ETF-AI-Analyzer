"""永豐投信官方 ETF 歷史配息與本金比例 Adapter。"""

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


SOURCE_ID = "sinopac_etf_dividend_document"
BASE_URL = "https://sitc.sinopac.com"
DIVIDEND_URL = f"{BASE_URL}/SinopacEtfs/Funds/DividenEtf"
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_FUND_ID_PATTERN = re.compile(r'u\.attr\("id"\)\s*!=\s*["\']([0-9A-Z]+)["\']')
_FUND_TITLE_PATTERN = re.compile(
    r"([^<>]+ETF基金)[（(]證[劵券]代碼：([0-9A-Z]+)[）)]", re.I,
)
_TABLE_PATTERN = re.compile(
    r'<table[^>]+id="divtable"[^>]*>(.*?)</table>', re.I | re.S,
)
_ROW_PATTERN = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
_CELL_PATTERN = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
_TAG_PATTERN = re.compile(r"<[^>]+>")


@dataclass(frozen=True, slots=True)
class SinopacFundMapping:
    etf_code: str
    fund_id: str
    fund_name: str


@dataclass(frozen=True, slots=True)
class SinopacDividendAmount:
    etf_code: str
    fund_name: str
    amount_per_unit: Decimal
    evaluation_date: date
    ex_dividend_date: date
    record_date: date
    payment_date: date
    frequency: str
    distributable_income_percent: Decimal
    principal_percent: Decimal
    information_basis: str = "ACTUAL_AMOUNT_AND_PRINCIPAL_SPLIT"


def _plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_PATTERN.sub(" ", value))).strip()


def parse_sinopac_fund_mapping(
    *, etf_code: str, html_text: str,
) -> SinopacFundMapping:
    """從官方 PCF 頁解析 ETF 代號、基金名稱及內部 fund ID。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    id_match = _FUND_ID_PATTERN.search(html_text)
    title_matches = _FUND_TITLE_PATTERN.findall(html_text)
    if id_match is None:
        raise ValueError(f"永豐官方 PCF 頁找不到 fund ID：{normalized}")
    for fund_name, stock_code in title_matches:
        if stock_code.upper() == normalized:
            return SinopacFundMapping(
                normalized, id_match.group(1), _plain_text(fund_name),
            )
    raise ValueError(f"永豐官方 PCF 頁找不到 ETF 名稱：{normalized}")


def parse_sinopac_dividend_amounts(
    *, etf_code: str, html_text: str,
) -> tuple[SinopacDividendAmount, ...]:
    """解析官方桌面版配息表；比例不推論為 54C 或 76W。"""

    normalized = etf_code.strip().upper()
    table_match = _TABLE_PATTERN.search(html_text)
    if table_match is None:
        raise ValueError("永豐官方配息頁找不到資料表")
    rows: list[SinopacDividendAmount] = []
    for row_html in _ROW_PATTERN.findall(table_match.group(1)):
        cells = [_plain_text(cell) for cell in _CELL_PATTERN.findall(row_html)]
        if len(cells) != 9:
            continue
        rows.append(SinopacDividendAmount(
            etf_code=normalized,
            fund_name=cells[0],
            amount_per_unit=Decimal(cells[1]),
            evaluation_date=date.fromisoformat(cells[2].replace("/", "-")),
            ex_dividend_date=date.fromisoformat(cells[3].replace("/", "-")),
            record_date=date.fromisoformat(cells[4].replace("/", "-")),
            payment_date=date.fromisoformat(cells[5].replace("/", "-")),
            frequency=cells[6],
            distributable_income_percent=Decimal(cells[7]),
            principal_percent=Decimal(cells[8]),
        ))
    return tuple(rows)


def _validate_response(response: httpx.Response, *, source) -> None:
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("永豐投信官方回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("永豐投信官方來源未回傳 HTML")


def fetch_sinopac_dividend_amounts(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[SinopacDividendAmount, ...]:
    """依 ETF 代號解析永豐官方 fund ID 與成立以來配息資料。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    source = get_actual_dividend_source(SOURCE_ID)
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    normalized = etf_code.strip().upper()
    client = httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    pcf = client.get(f"{BASE_URL}/SinopacEtfs/Etfs/SinglePcf/{normalized}")
    _validate_response(pcf, source=source)
    mapping = parse_sinopac_fund_mapping(etf_code=normalized, html_text=pcf.text)
    history = client.post(
        DIVIDEND_URL,
        data={"fundId": mapping.fund_id, "range": "5", "hdnTimeRange": "5"},
    )
    _validate_response(history, source=source)
    return parse_sinopac_dividend_amounts(
        etf_code=mapping.etf_code, html_text=history.text,
    )
