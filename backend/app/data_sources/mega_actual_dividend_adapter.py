"""兆豐投信官方 ETF 歷史配息金額 Adapter。"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "mega_etf_dividend_document"
CATALOG_URL = "https://www.megafunds.com.tw/MEGA/etf/"
DIVIDEND_URL = "https://www.megafunds.com.tw/MEGA/etf/income.aspx"
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
_OPTION_PATTERN = re.compile(
    r'<option(?:\s+selected="selected")?\s+value="([^"]+)">(.*?)</option>',
    re.I | re.S,
)
_ROW_PATTERN = re.compile(r'<tr class="tr-est"[^>]*>(.*?)</tr>', re.I | re.S)
_CELL_PATTERN = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
_TAG_PATTERN = re.compile(r"<[^>]+>")


@dataclass(frozen=True, slots=True)
class MegaFundMapping:
    etf_code: str
    fund_name: str
    internal_id: str


@dataclass(frozen=True, slots=True)
class MegaDividendAmount:
    etf_code: str
    amount_per_unit: Decimal
    ex_dividend_date: date
    yield_percent: Decimal
    fill_date: date | None
    fill_days: int | None
    dividend_54c_amount: Decimal | None
    interest_5a_amount: Decimal | None
    information_basis: str = "ACTUAL_AMOUNT_ONLY"


def _plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_PATTERN.sub(" ", value))).strip()


def _normalized_name(value: str) -> str:
    compact = re.sub(r"\s+", "", _plain_text(value))
    return re.split(r"[（(](?:本基金|基金)", compact, maxsplit=1)[0]


class _HiddenInputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "input":
            return
        attributes = dict(attrs)
        if (attributes.get("type") or "").lower() != "hidden":
            return
        name = attributes.get("name")
        if name:
            self.values[name] = attributes.get("value") or ""


class _ProductCatalogParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.products: list[tuple[str, str]] = []
        self._product_depth = 0
        self._detail_depth = 0
        self._detail_text: list[str] = []
        self._cells: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "div":
            return
        classes = (dict(attrs).get("class") or "").split()
        if self._product_depth:
            self._product_depth += 1
        elif "product-detail" in classes:
            self._product_depth = 1
            self._cells = []
        if self._product_depth and "detail-item" in classes:
            self._detail_depth = self._product_depth
            self._detail_text = []

    def handle_data(self, data: str) -> None:
        if self._detail_depth:
            self._detail_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "div" or not self._product_depth:
            return
        if self._detail_depth == self._product_depth:
            self._cells.append(_plain_text(" ".join(self._detail_text)))
            self._detail_depth = 0
            self._detail_text = []
        self._product_depth -= 1
        if self._product_depth == 0 and len(self._cells) >= 2:
            self.products.append((self._cells[0], self._cells[1]))


def parse_mega_fund_mapping(
    *, etf_code: str, catalog_html: str, dividend_html: str,
) -> MegaFundMapping:
    """以官方基金名稱連接證券代號、產品頁與配息頁內部 ID。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    catalog_parser = _ProductCatalogParser()
    catalog_parser.feed(catalog_html)
    catalog_names = {
        code.upper(): name
        for code, name in catalog_parser.products
        if _ETF_CODE_PATTERN.fullmatch(code)
    }
    try:
        fund_name = catalog_names[normalized]
    except KeyError as error:
        raise ValueError(f"兆豐 ETF 總覽找不到證券代號：{normalized}") from error

    wanted_name = _normalized_name(fund_name)
    for internal_id, option_name in _OPTION_PATTERN.findall(dividend_html):
        if _normalized_name(option_name) == wanted_name:
            return MegaFundMapping(normalized, fund_name, internal_id)
    raise ValueError(f"兆豐配息頁找不到基金內部 ID：{normalized}")


def parse_mega_dividend_amounts(
    *, etf_code: str, html_text: str,
) -> tuple[MegaDividendAmount, ...]:
    """解析官方歷史配息表；未揭露的所得組成維持空值。"""

    normalized = etf_code.strip().upper()
    rows: list[MegaDividendAmount] = []
    for row_html in _ROW_PATTERN.findall(html_text):
        cells = [_plain_text(value) for value in _CELL_PATTERN.findall(row_html)]
        if len(cells) != 8 or not re.fullmatch(r"20\d{2}/\d{2}/\d{2}", cells[1]):
            continue

        def optional_decimal(value: str) -> Decimal | None:
            return None if value in {"", "-"} else Decimal(value)

        rows.append(MegaDividendAmount(
            etf_code=normalized,
            ex_dividend_date=date.fromisoformat(cells[1].replace("/", "-")),
            amount_per_unit=Decimal(cells[2]),
            yield_percent=Decimal(cells[3]),
            fill_date=(
                None if cells[4] in {"", "-"}
                else date.fromisoformat(cells[4].replace("/", "-"))
            ),
            fill_days=None if cells[5] in {"", "-"} else int(cells[5]),
            dividend_54c_amount=optional_decimal(cells[6]),
            interest_5a_amount=optional_decimal(cells[7]),
        ))
    return tuple(rows)


def _validate_response(response: httpx.Response, *, source) -> None:
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("兆豐投信官方回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("兆豐投信官方來源未回傳 HTML")


def fetch_mega_dividend_amounts(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[MegaDividendAmount, ...]:
    """依 ETF 代號自動解析兆豐官方內部 ID 與歷史配息金額。"""

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
    catalog = client.get(CATALOG_URL)
    dividend = client.get(DIVIDEND_URL)
    _validate_response(catalog, source=source)
    _validate_response(dividend, source=source)
    mapping = parse_mega_fund_mapping(
        etf_code=etf_code,
        catalog_html=catalog.text,
        dividend_html=dividend.text,
    )
    hidden_parser = _HiddenInputParser()
    hidden_parser.feed(dividend.text)
    form = hidden_parser.values
    form.update({
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ddListDividendTitle",
        "ctl00$ContentPlaceHolder1$ddListDividendTitle": mapping.internal_id,
        "ctl00$ContentPlaceHolder1$ddListFundType": "",
        "ctl00$ContentPlaceHolder1$ddListTitmeLimit": "0",
    })
    selected = client.post(DIVIDEND_URL, data=form)
    _validate_response(selected, source=source)
    return parse_mega_dividend_amounts(
        etf_code=mapping.etf_code, html_text=selected.text,
    )
