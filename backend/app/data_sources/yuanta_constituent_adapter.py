"""元大投信官方 PCF API 成分股 Adapter。"""

import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from backend.app.data_sources.openapi import create_ssl_context
from backend.app.models.etf_constituent import ETFConstituentSnapshotCreate


SOURCE_ID = "yuanta_official_pcf"
API_URL = "https://etfapi.yuantaetfs.com/ectranslation/api/bridge"
PRODUCT_URL_TEMPLATE = "https://www.yuantaetfs.com/product/detail/{etf_code}/ratio"
MINIMUM_STOCK_WEIGHT_PCT = Decimal("90")


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"元大官方 PCF 缺少 {field}")
    return value


def parse_yuanta_constituent_payload(
    payload: Any,
    *,
    etf_code: str,
    source_url: str,
    fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    """解析官方 PCF 股票權重，並拒絕不完整或錯檔的回應。"""

    normalized_code = etf_code.strip().upper()
    if not re.fullmatch(r"[0-9A-Z]{4,10}", normalized_code):
        raise ValueError("ETF 代號格式不正確")
    root = _require_mapping(payload, "回應物件")
    pcf = _require_mapping(root.get("PCF"), "PCF")
    returned_code = str(pcf.get("markcd") or "").strip().upper()
    if returned_code != normalized_code:
        raise ValueError(
            f"元大官方 PCF 回傳代號 {returned_code or '空值'}，"
            f"與要求的 {normalized_code} 不符"
        )
    trade_date = str(pcf.get("trandate") or "")
    if not re.fullmatch(r"\d{8}", trade_date):
        raise ValueError("元大官方 PCF 缺少有效交易日期")

    weights = _require_mapping(root.get("FundWeights"), "FundWeights")
    rows = weights.get("StockWeights")
    if not isinstance(rows, list) or not rows:
        raise ValueError("元大官方 PCF 沒有股票權重")

    positions = []
    for rank, row in enumerate(rows, start=1):
        item = _require_mapping(row, f"StockWeights[{rank - 1}]")
        code = str(item.get("code") or "").strip().upper()
        name = str(item.get("name") or "").strip()
        weight = item.get("weights")
        if not code or not name or weight is None:
            raise ValueError(f"元大官方 PCF 第 {rank} 筆股票權重欄位不完整")
        positions.append(
            {
                "constituent_id": code,
                "constituent_name": name,
                "weight_pct": Decimal(str(weight)),
                "rank": rank,
            }
        )

    total_weight = sum(item["weight_pct"] for item in positions)
    if total_weight < MINIMUM_STOCK_WEIGHT_PCT:
        raise ValueError(
            f"元大官方 PCF 股票權重僅 {total_weight}%，疑似資料不完整"
        )

    return ETFConstituentSnapshotCreate(
        etf_code=normalized_code,
        as_of_date=date.fromisoformat(
            f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
        ),
        source_id=SOURCE_ID,
        source_url=source_url,
        fetched_at=fetched_at,
        positions=positions,
    )


def fetch_yuanta_constituent_snapshot(
    etf_code: str,
    *,
    timeout_seconds: float = 30,
    fetched_at: datetime | None = None,
) -> ETFConstituentSnapshotCreate:
    normalized_code = etf_code.strip().upper()
    source_url = PRODUCT_URL_TEMPLATE.format(etf_code=normalized_code)
    response = httpx.get(
        API_URL,
        params={
            "APIType": "ETFAPI",
            "CompanyName": "YUANTAFUNDS",
            "PageName": f"/product/detail/{normalized_code}/ratio",
            "DeviceId": "null",
            "FuncId": "PCF/Daily",
            "AppName": "ETF",
            "Device": "3",
            "Platform": "ETF",
            "ticker": normalized_code,
        },
        timeout=timeout_seconds,
        follow_redirects=True,
        verify=create_ssl_context(allow_legacy_x509=True),
        headers={
            "Accept": "application/json",
            "User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-data-downloader)",
        },
    )
    response.raise_for_status()
    return parse_yuanta_constituent_payload(
        response.json(),
        etf_code=normalized_code,
        source_url=source_url,
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )
