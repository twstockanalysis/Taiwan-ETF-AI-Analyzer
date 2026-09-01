"""以 ETF 代號直接查詢的官方成分股來源。"""

import html
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urljoin

import httpx

from backend.app.data_sources.openapi import create_ssl_context
from backend.app.models.etf_constituent import ETFConstituentSnapshotCreate


MINIMUM_STOCK_WEIGHT_PCT = Decimal("90")
MINIMUM_FUBON_STOCK_WEIGHT_PCT = Decimal("85")
USER_AGENT = "TW-ETF-AI-Analyzer/0.1 (official-data-downloader)"

SINOPAC_URL = "https://sitc.sinopac.com/SinopacEtfs/Etfs/Pcf/{etf_code}"
TAISHIN_URL = "https://www.tsit.com.tw/ETF/Home/ETFSeriesDetail/{etf_code}"
CTBC_URL = "https://www.ctbcinvestments.com.tw/CTWEB/Content/ETF/pcd.aspx"
FUBON_PCF_URL = "https://websys.fsit.com.tw/FubonETF/Trade/Pcf.aspx"
NOMURA_API_URL = (
    "https://www.nomurafunds.com.tw/API/ETFAPI/api/Fund/GetFundAssets"
)
NOMURA_SOURCE_URL = "https://www.nomurafunds.com.tw/ETFWEB/pcf"


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.inputs: dict[str, str] = {}
        self.links: list[str] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        values = dict(attrs)
        if tag == "table" and self._table is None:
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []
        elif tag == "input" and values.get("id"):
            self.inputs[values["id"]] = values.get("value") or ""
        elif tag == "a" and values.get("href"):
            self.links.append(html.unescape(values["href"] or ""))

    def handle_data(self, data: str):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str):
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if any(self._row):
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None


def _normalize_code(etf_code: str) -> str:
    value = etf_code.strip().upper()
    if not re.fullmatch(r"[0-9A-Z]{4,10}", value):
        raise ValueError("ETF 代號格式不正確")
    return value


def _parse_date(value: str, issuer: str) -> date:
    match = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", value)
    if match is None:
        raise ValueError(f"{issuer}官方持股缺少有效資料日期")
    return date(*(int(part) for part in match.groups()))


def _stock_table(
    tables: list[list[list[str]]], expected_headers: tuple[str, ...], issuer: str
) -> list[list[str]]:
    for table in tables:
        if table and all(header in table[0] for header in expected_headers):
            return table
    raise ValueError(f"{issuer}官方持股找不到股票權重表")


def _positions(
    table: list[list[str]], *, code_index: int, name_index: int,
    weight_index: int, issuer: str,
    minimum_stock_weight_pct: Decimal = MINIMUM_STOCK_WEIGHT_PCT,
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for row in table[1:]:
        if len(row) <= max(code_index, name_index, weight_index):
            continue
        code = re.sub(r"\s+TT$", "", row[code_index].strip().upper())
        name = row[name_index].strip()
        raw_weight = row[weight_index].replace("%", "").replace(",", "").strip()
        if not code or not name or "合計" in code:
            continue
        try:
            weight = Decimal(raw_weight)
        except InvalidOperation as error:
            raise ValueError(f"{issuer}官方持股包含無效股票權重：{raw_weight}") from error
        values.append({
            "constituent_id": code,
            "constituent_name": name,
            "weight_pct": weight,
            "rank": len(values) + 1,
        })
    if not values:
        raise ValueError(f"{issuer}官方持股沒有股票權重")
    total = sum(item["weight_pct"] for item in values)
    if total < minimum_stock_weight_pct:
        raise ValueError(f"{issuer}官方持股股票權重僅 {total}%，疑似資料不完整")
    return values


def _snapshot(
    etf_code: str, issuer: str, source_id: str, source_url: str,
    as_of_date: date, positions: list[dict[str, Any]], fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    return ETFConstituentSnapshotCreate(
        etf_code=etf_code,
        as_of_date=as_of_date,
        source_id=source_id,
        source_url=source_url,
        fetched_at=fetched_at,
        positions=positions,
    )


def _parse_html_source(
    content: str, *, etf_code: str, issuer: str, source_id: str,
    source_url: str, fetched_at: datetime, expected_headers: tuple[str, ...],
    date_value: str, weight_index: int,
    minimum_stock_weight_pct: Decimal = MINIMUM_STOCK_WEIGHT_PCT,
) -> ETFConstituentSnapshotCreate:
    if etf_code not in content.upper():
        raise ValueError(f"{issuer}官方持股回應與要求的 {etf_code} 不符")
    parser = _TableParser()
    parser.feed(content)
    table = _stock_table(parser.tables, expected_headers, issuer)
    return _snapshot(
        etf_code, issuer, source_id, source_url,
        _parse_date(date_value, issuer),
        _positions(
            table, code_index=0, name_index=1,
            weight_index=weight_index, issuer=issuer,
            minimum_stock_weight_pct=minimum_stock_weight_pct,
        ),
        fetched_at,
    )


def parse_sinopac_constituent_html(
    content: str, *, etf_code: str, source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    normalized = _normalize_code(etf_code)
    date_match = re.search(r"資料日期[：:]\s*(20\d{2}/\d{1,2}/\d{1,2})", content)
    return _parse_html_source(
        content, etf_code=normalized, issuer="永豐", source_id="sinopac_official_pcf",
        source_url=source_url, fetched_at=fetched_at,
        expected_headers=("證券代碼", "證券名稱", "佔基金淨資產之權重(%)"),
        date_value=date_match.group(1) if date_match else "", weight_index=3,
    )


def parse_taishin_constituent_html(
    content: str, *, etf_code: str, source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    normalized = _normalize_code(etf_code)
    parser = _TableParser()
    parser.feed(content)
    return _parse_html_source(
        content, etf_code=normalized, issuer="台新", source_id="taishin_official_holdings",
        source_url=source_url, fetched_at=fetched_at,
        expected_headers=("代號", "名稱", "持股權重"),
        date_value=parser.inputs.get("NAV_DATE", ""), weight_index=3,
    )


def parse_ctbc_constituent_html(
    content: str, *, etf_code: str, source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    normalized = _normalize_code(etf_code)
    date_match = re.search(
        r'id=["\']Label_AUM01["\'][^>]*>\s*(20\d{2}/\d{1,2}/\d{1,2})', content,
    )
    return _parse_html_source(
        content, etf_code=normalized, issuer="中國信託", source_id="ctbc_official_pcf",
        source_url=source_url, fetched_at=fetched_at,
        expected_headers=("股票代碼", "股票名稱", "權重(%)"),
        date_value=date_match.group(1) if date_match else "", weight_index=3,
    )


def parse_fubon_constituent_html(
    content: str, *, etf_code: str, source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    normalized = _normalize_code(etf_code)
    date_match = re.search(r"資料日期[：:]\s*(20\d{2}/\d{1,2}/\d{1,2})", content)
    result = _parse_html_source(
        content, etf_code=normalized, issuer="富邦", source_id="fubon_official_assets",
        source_url=source_url, fetched_at=fetched_at,
        expected_headers=("股票代碼", "股票名稱", "權重(%)"),
        date_value=date_match.group(1) if date_match else "", weight_index=4,
        minimum_stock_weight_pct=MINIMUM_FUBON_STOCK_WEIGHT_PCT,
    )
    stock_total = sum(item.weight_pct for item in result.positions)
    if stock_total < MINIMUM_STOCK_WEIGHT_PCT:
        parser = _TableParser()
        parser.feed(content)
        non_stock_headers = {"期貨代碼", "債券代碼", "基金代碼", "ETF代碼"}
        has_non_stock_positions = any(
            len(table) > 1 and any(header in table[0] for header in non_stock_headers)
            for table in parser.tables
        )
        if not has_non_stock_positions:
            raise ValueError("富邦官方股票權重低於 90%，且缺少非股票資產表供對帳")
    return result


def parse_nomura_constituent_payload(
    payload: Any, *, etf_code: str, source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    normalized = _normalize_code(etf_code)
    if not isinstance(payload, dict) or payload.get("StatusCode") != 0:
        raise ValueError("野村官方持股 API 回應失敗")
    entries = payload.get("Entries")
    if not isinstance(entries, dict) or str(entries.get("FundID", "")).upper() != normalized:
        raise ValueError(f"野村官方持股回應與要求的 {normalized} 不符")
    data = entries.get("Data")
    tables = data.get("Table") if isinstance(data, dict) else None
    if not isinstance(tables, list):
        raise ValueError("野村官方持股缺少股票權重表")
    stock = next(
        (item for item in tables if isinstance(item, dict) and item.get("TableTitle") == "股票"),
        None,
    )
    if not isinstance(stock, dict) or not isinstance(stock.get("Rows"), list):
        raise ValueError("野村官方持股缺少股票權重表")
    table = [["股票代號", "股票名稱", "股數", "權重(%)"], *stock["Rows"]]
    return _snapshot(
        normalized, "野村", "nomura_official_fund_assets", source_url,
        _parse_date(str(stock.get("NavDate") or ""), "野村"),
        _positions(table, code_index=0, name_index=1, weight_index=3, issuer="野村"),
        fetched_at,
    )


def _get(url: str, *, timeout_seconds: float, params: dict[str, str] | None = None):
    response = httpx.get(
        url, params=params, timeout=timeout_seconds, follow_redirects=True,
        verify=create_ssl_context(allow_legacy_x509=True),
        headers={"Accept": "text/html", "User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return response


def fetch_sinopac_constituent_snapshot(etf_code: str, *, timeout_seconds: float = 30,
                                        fetched_at: datetime | None = None):
    code = _normalize_code(etf_code)
    url = SINOPAC_URL.format(etf_code=code)
    return parse_sinopac_constituent_html(
        _get(url, timeout_seconds=timeout_seconds).text, etf_code=code,
        source_url=url, fetched_at=fetched_at or datetime.now(timezone.utc),
    )


def fetch_taishin_constituent_snapshot(etf_code: str, *, timeout_seconds: float = 30,
                                       fetched_at: datetime | None = None):
    code = _normalize_code(etf_code)
    url = TAISHIN_URL.format(etf_code=code)
    return parse_taishin_constituent_html(
        _get(url, timeout_seconds=timeout_seconds).text, etf_code=code,
        source_url=url, fetched_at=fetched_at or datetime.now(timezone.utc),
    )


def fetch_ctbc_constituent_snapshot(etf_code: str, *, timeout_seconds: float = 30,
                                    fetched_at: datetime | None = None):
    code = _normalize_code(etf_code)
    response = _get(CTBC_URL, timeout_seconds=timeout_seconds, params={"ETF_ID": code})
    return parse_ctbc_constituent_html(
        response.text, etf_code=code, source_url=str(response.url),
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )


def fetch_fubon_constituent_snapshot(etf_code: str, *, timeout_seconds: float = 30,
                                     fetched_at: datetime | None = None):
    code = _normalize_code(etf_code)
    pcf = _get(
        FUBON_PCF_URL, timeout_seconds=timeout_seconds,
        params={"lan": "TW", "stkId": code},
    )
    parser = _TableParser()
    parser.feed(pcf.text)
    link = next((value for value in parser.links if "Assets.aspx" in value), None)
    if link is None:
        raise ValueError("富邦官方 PCF 找不到基金資產連結")
    assets_url = urljoin(str(pcf.url), link)
    assets = _get(assets_url, timeout_seconds=timeout_seconds)
    return parse_fubon_constituent_html(
        assets.text, etf_code=code, source_url=str(assets.url),
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )


def fetch_nomura_constituent_snapshot(etf_code: str, *, timeout_seconds: float = 30,
                                      fetched_at: datetime | None = None):
    code = _normalize_code(etf_code)
    response = httpx.post(
        NOMURA_API_URL, json={"FundID": code, "SearchDate": None},
        timeout=timeout_seconds, follow_redirects=True,
        verify=create_ssl_context(allow_legacy_x509=True),
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return parse_nomura_constituent_payload(
        response.json(), etf_code=code, source_url=NOMURA_SOURCE_URL,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )


DIRECT_CONSTITUENT_FETCHERS: dict[str, Callable[..., ETFConstituentSnapshotCreate]] = {
    "sinopac": fetch_sinopac_constituent_snapshot,
    "taishin": fetch_taishin_constituent_snapshot,
    "ctbc": fetch_ctbc_constituent_snapshot,
    "fubon": fetch_fubon_constituent_snapshot,
    "nomura": fetch_nomura_constituent_snapshot,
}
