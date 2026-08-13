"""玉山投信官方 ETF 配息 JSON API Adapter。"""

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


SOURCE_ID = "esun_etf_dividend_document"
API_BASE_URL = "https://www.esunam.com/ETFAPI"
MAX_RESPONSE_BYTES = 3_000_000
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")


@dataclass(frozen=True, slots=True)
class EsunDividendAmount:
    etf_code: str
    fund_name: str
    fund_no: str
    evaluation_date: date
    last_subscription_date: date
    ex_dividend_date: date
    payment_date: date
    amount_per_unit: Decimal
    distribution_rate_percent: Decimal | None
    frequency: str
    information_basis: str = "ACTUAL_AMOUNT_ONLY"


def _parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _validated_entries(payload: dict, *, label: str) -> list[dict]:
    if payload.get("StatusCode", 0) != 0:
        raise ValueError(f"玉山官方{label} API 回傳失敗狀態")
    entries = payload.get("Entries")
    if not isinstance(entries, list):
        raise ValueError(f"玉山官方{label} API 缺少 Entries")
    return entries


def parse_esun_dividend_amounts(
    *, etf_code: str, overview_payload: dict, yield_payload: dict,
) -> tuple[EsunDividendAmount, ...]:
    """解析官方基金編號對照及配息歷史，不推論所得組成。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    overview = _validated_entries(overview_payload, label="ETF 總覽")
    histories = _validated_entries(yield_payload, label="配息")
    fund = next(
        (item for item in overview
         if str(item.get("StcokNo", "")).strip().upper() == normalized),
        None,
    )
    if fund is None:
        return ()
    fund_no = str(fund.get("FundNo", "")).strip()
    rows: list[EsunDividendAmount] = []
    for item in histories:
        if str(item.get("CNo", "")).strip() != fund_no:
            continue
        rate_text = str(item.get("CInterestOfMonth", "")).strip()
        rows.append(EsunDividendAmount(
            etf_code=normalized,
            fund_name=str(item.get("CFullName", "")).strip(),
            fund_no=fund_no,
            evaluation_date=_parse_date(item["CInterestDt"]),
            last_subscription_date=_parse_date(item["CLastSubscriptionDt"]),
            ex_dividend_date=_parse_date(item["CExDividendDt"]),
            payment_date=_parse_date(item["CReleaseDt"]),
            amount_per_unit=Decimal(str(item["CInterestOfUnit"])),
            distribution_rate_percent=(
                None if not rate_text or rate_text == "-"
                else Decimal(rate_text.removesuffix("%"))
            ),
            frequency=str(item.get("CCgDividendTypeStr", "")).strip(),
        ))
    return tuple(rows)


def _post_json(path: str, payload: dict, *, source) -> dict:
    response = httpx.post(
        f"{API_BASE_URL}/{path}", json=payload, timeout=30.0,
        follow_redirects=True, verify=create_ssl_context(),
        headers={"User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)"},
    )
    response.raise_for_status()
    validate_official_source_url(source, str(response.url))
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("玉山官方 ETF API 回應超過容量上限")
    if "application/json" not in response.headers.get("content-type", "").lower():
        raise ValueError("玉山官方 ETF API 未回傳 JSON")
    return response.json()


def fetch_esun_dividend_amounts(
    *, etf_code: str, allow_network: bool = False,
) -> tuple[EsunDividendAmount, ...]:
    """依上市 ETF 代號查詢玉山官方配息歷史。"""

    if not allow_network:
        raise ValueError("網路查詢必須明確設定 allow_network=True")
    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    source = get_actual_dividend_source(SOURCE_ID)
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式查詢")
    overview = _post_json("GetETFOverview", {
        "PageSize": 999, "ETFInvestmentIDs": [], "ETFFundTypeIDs": [],
        "ETFFundDividendIDs": [], "ETFInvestAreaIDs": [],
        "Keyword": normalized, "KeywordId": 0, "SortColName": "",
        "IsDesc": False,
    }, source=source)
    history = _post_json("GetETFFundYieldList", {
        "FundType": -1, "FundNo": "", "SearchType": 2, "PageSize": 9999,
    }, source=source)
    return parse_esun_dividend_amounts(
        etf_code=normalized, overview_payload=overview, yield_payload=history,
    )
