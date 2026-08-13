"""聯博投信官方 ETF 配息 JSON API Adapter。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy, get_actual_dividend_source,
)
from backend.app.data_sources.issuer_landing_page_discovery import _AnchorParser
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import validate_official_source_url

SOURCE_ID = "alliancebernstein_etf_dividend_document"
API_URL = "https://webapi.alliancebernstein.com/v2/funds/tw/zh-tw/investor/{isin}/distributions"
MAX_RESPONSE_BYTES = 1_000_000
_ISIN_PATTERN = re.compile(r"^TW[0-9A-Z]{10}$")
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")
LANDING_URL = "https://www.abfunds.com.tw/zh-tw/home.html"


@dataclass(frozen=True, slots=True)
class AllianceBernsteinDividendAmount:
    isin: str
    ex_dividend_date: date
    payment_date: date | None
    amount_per_unit: Decimal
    distribution_yield_percent: Decimal | None
    information_basis: str = "ACTUAL_AMOUNT_ONLY"


@dataclass(frozen=True, slots=True)
class AllianceBernsteinDividendResult:
    isin: str
    as_of_date: date | None
    next_distribution_date: date | None
    distributions: tuple[AllianceBernsteinDividendAmount, ...]


def _date_or_none(value: object) -> date | None:
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value)[:10])


def parse_alliancebernstein_dividends(
    *, isin: str, payload: dict,
) -> AllianceBernsteinDividendResult:
    """解析官方回應，並允許尚未首次配息的有效空陣列。"""
    normalized = isin.strip().upper()
    if not _ISIN_PATTERN.fullmatch(normalized):
        raise ValueError("聯博 ETF ISIN 格式錯誤")
    raw_rows = payload.get("distributions")
    if not isinstance(raw_rows, list):
        raise ValueError("聯博配息 API 缺少 distributions 陣列")
    rows: list[AllianceBernsteinDividendAmount] = []
    for item in raw_rows:
        if not isinstance(item, dict):
            raise ValueError("聯博配息 API 資料列格式錯誤")
        ex_date = _date_or_none(item.get("exDate"))
        amount = item.get("distributionValue")
        if ex_date is None or amount in (None, ""):
            raise ValueError("聯博配息 API 資料列缺少除息日或金額")
        raw_yield = item.get("distributionYield")
        rows.append(AllianceBernsteinDividendAmount(
            isin=normalized,
            ex_dividend_date=ex_date,
            payment_date=_date_or_none(
                item.get("payDate") or item.get("nextDistributionDate")
            ),
            amount_per_unit=Decimal(str(amount)),
            distribution_yield_percent=(
                Decimal(str(raw_yield)) if raw_yield not in (None, "") else None
            ),
        ))
    return AllianceBernsteinDividendResult(
        isin=normalized,
        as_of_date=_date_or_none(payload.get("asOfDate")),
        next_distribution_date=_date_or_none(payload.get("nextDistributionDate")),
        distributions=tuple(rows),
    )


def resolve_alliancebernstein_isin(
    *, etf_code: str, html_text: str,
) -> str:
    """從聯博官方基金連結解析 ETF 代號對應的台灣 ISIN。"""
    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    parser = _AnchorParser()
    parser.feed(html_text)
    for href, title in parser.links:
        if normalized not in f"{title} {href}".upper():
            continue
        for value in re.findall(r"TW[0-9A-Z]{10}", href.upper()):
            if _ISIN_PATTERN.fullmatch(value):
                return value
    raise ValueError(f"聯博官方頁找不到 ETF ISIN：{normalized}")


def fetch_alliancebernstein_dividends(
    *, etf_code: str, allow_network: bool = False,
) -> AllianceBernsteinDividendResult:
    source = get_actual_dividend_source(SOURCE_ID)
    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    landing = httpx.get(
        LANDING_URL, timeout=30.0, follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    landing.raise_for_status()
    validate_official_source_url(source, str(landing.url))
    if len(landing.content) > MAX_RESPONSE_BYTES:
        raise ValueError("聯博官方基金頁回應超過容量上限")
    isin = resolve_alliancebernstein_isin(
        etf_code=etf_code, html_text=landing.text
    )
    response = httpx.get(
        API_URL.format(isin=isin), timeout=30.0, follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("聯博官方配息 API 回應超過容量上限")
    return parse_alliancebernstein_dividends(
        isin=isin, payload=response.json()
    )
