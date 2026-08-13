"""野村投信官方 ETF 配息 JSON API Adapter。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
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


SOURCE_ID = "nomura_etf_dividend_document"
API_URL = "https://www.nomurafunds.com.tw/API/ETFAPI/api/Fund/GetFundYield"
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")


@dataclass(frozen=True, slots=True)
class NomuraDividendAmount:
    etf_code: str
    fund_name: str
    base_month: str
    evaluation_date: date
    ex_dividend_date: date
    payment_date: date
    amount_per_unit: Decimal
    distribution_rate_percent: Decimal | None
    frequency_per_year: int | None
    information_basis: str = "ACTUAL_AMOUNT_ONLY"


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.replace("/", "-"))


def parse_nomura_dividend_amounts(
    *, etf_code: str, payload: dict,
) -> tuple[NomuraDividendAmount, ...]:
    """解析官方 GetFundYield 回應，不推論未提供的所得組成。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    if payload.get("StatusCode", 0) != 0:
        raise ValueError("野村官方配息 API 回傳失敗狀態")
    entries = payload.get("Entries")
    if not isinstance(entries, list):
        raise ValueError("野村官方配息 API 缺少 Entries")
    rows: list[NomuraDividendAmount] = []
    for fund in entries:
        if str(fund.get("CFundNo", "")).upper() != normalized:
            continue
        fund_name = str(fund.get("CShortName", "")).strip()
        for item in fund.get("YieldData") or []:
            rate = item.get("CCurrentDy")
            rows.append(NomuraDividendAmount(
                etf_code=normalized,
                fund_name=fund_name,
                base_month=str(item["CBaseDate"]),
                evaluation_date=_parse_date(item["CValuationDate"]),
                ex_dividend_date=_parse_date(item["CExDate"]),
                payment_date=_parse_date(item["CPayableDate"]),
                amount_per_unit=Decimal(str(item["CPerShare"])),
                distribution_rate_percent=(
                    None if rate is None else Decimal(str(rate)) * Decimal("100")
                ),
                frequency_per_year=(
                    None if item.get("CDvdSetting") is None
                    else int(item["CDvdSetting"])
                ),
            ))
    return tuple(rows)


def fetch_nomura_dividend_amounts(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[NomuraDividendAmount, ...]:
    """依 ETF 代號查詢野村官方 GetFundYield API。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    source = get_actual_dividend_source(SOURCE_ID)
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    response = httpx.post(
        API_URL,
        json={
            "Type": 2,
            "Keyword": normalized,
            "FundNo": "",
            "StartDate": "2000-01-01T00:00:00.000Z",
            "EndDate": "2100-12-31T00:00:00.000Z",
            "FundType": 0,
            "PageIndex": 1,
            "PageSize": 9999,
            "IsPagination": True,
            "SortColName": "",
            "IsDesc": False,
        },
        timeout=30.0,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("野村官方配息 API 回應超過容量上限")
    if "application/json" not in response.headers.get("content-type", "").lower():
        raise ValueError("野村官方配息 API 未回傳 JSON")
    return parse_nomura_dividend_amounts(
        etf_code=normalized, payload=response.json(),
    )
