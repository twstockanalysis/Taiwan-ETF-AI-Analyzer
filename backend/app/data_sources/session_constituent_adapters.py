"""需短效 token 或 antiforgery session 的官方 ETF 成分股來源。"""

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import httpx

from backend.app.data_sources.direct_constituent_adapters import (
    USER_AGENT,
    _normalize_code,
    _parse_date,
    _positions,
    _snapshot,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.models.etf_constituent import ETFConstituentSnapshotCreate


HNH_API_BASE_URL = "https://www.hnfunds.com.tw/WEB_API/HN_OW_PROD"
HNH_PUBLIC_CLIENT_ID = "WFPAPIPublicClient"
ALLIANZ_API_BASE_URL = "https://etf.allianzgi.com.tw/webapi/api"
ALLIANZ_SOURCE_URL = "https://etf.allianzgi.com.tw/etf-info/{fund_id}?tab=4"
MAX_RESPONSE_BYTES = 5_000_000


def _ensure_response_size(response: httpx.Response, issuer: str) -> None:
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError(f"{issuer}官方成分股回應超過容量上限")


def parse_hnh_system_token(payload: Any) -> str:
    if not isinstance(payload, dict) or str(payload.get("ResultCode", "")) != "00":
        raise ValueError("華南永昌官方系統 token 回應失敗")
    token = str(payload.get("access_token", "")).strip()
    try:
        expires_in = int(payload.get("expires_in", 0))
    except (TypeError, ValueError) as error:
        raise ValueError("華南永昌官方系統 token 缺少有效期") from error
    if not token or expires_in <= 0:
        raise ValueError("華南永昌官方系統 token 缺少有效期")
    return token


def parse_hnh_constituent_payload(
    payload: Any, *, etf_code: str, source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    code = _normalize_code(etf_code)
    if not isinstance(payload, dict) or str(payload.get("ResultCode", "")) != "00":
        raise ValueError("華南永昌官方 PCF API 回應失敗")
    data = payload.get("Data")
    pcf_rows = data.get("pcf") if isinstance(data, dict) else None
    if not isinstance(pcf_rows, list) or len(pcf_rows) != 1:
        raise ValueError("華南永昌官方 PCF 缺少唯一基金資料")
    pcf = pcf_rows[0]
    if not isinstance(pcf, dict) or str(pcf.get("ETFID", "")).strip().upper() != code:
        raise ValueError(f"華南永昌官方 PCF 回應與要求的 {code} 不符")
    stocks = data.get("StockList")
    if not isinstance(stocks, list) or not stocks:
        raise ValueError("華南永昌官方 PCF 缺少股票權重表")
    table = [["股票代號", "股票名稱", "權重(%)"]]
    for row in stocks:
        if not isinstance(row, dict):
            raise ValueError("華南永昌官方 PCF 包含無效資料列")
        try:
            weight_pct = Decimal(str(row.get("Weight", ""))) * 100
        except InvalidOperation as error:
            raise ValueError("華南永昌官方 PCF 包含無效股票權重") from error
        table.append([
            str(row.get("StockNo", "")).strip(),
            str(row.get("StockName", "")).strip(),
            str(weight_pct),
        ])
    return _snapshot(
        code, "華南永昌", "hnh_official_pcf_api", source_url,
        _parse_date(str(pcf.get("BalDate", "")), "華南永昌"),
        _positions(
            table, code_index=0, name_index=1, weight_index=2,
            issuer="華南永昌",
        ),
        fetched_at,
    )


def parse_allianz_mapping(*, etf_code: str, catalog_payload: Any) -> str:
    code = _normalize_code(etf_code)
    if not isinstance(catalog_payload, dict):
        raise ValueError("安聯官方 ETF 總覽 API 回應失敗")
    entries = catalog_payload.get("Entries")
    if catalog_payload.get("StatusCode") != 0 or not isinstance(entries, list):
        raise ValueError("安聯官方 ETF 總覽 API 回應失敗")
    matches = [
        row for row in entries if isinstance(row, dict)
        and str(row.get("CSecuritiesCode", "")).strip().upper() == code
    ]
    if len(matches) != 1:
        raise ValueError(f"安聯官方 ETF 總覽找不到唯一證券代號：{code}")
    fund_id = str(matches[0].get("CFundNo", "")).strip().upper()
    if not re.fullmatch(r"E\d{4}", fund_id):
        raise ValueError("安聯官方 ETF 總覽包含無效 FundNo")
    return fund_id


def parse_allianz_constituent_payload(
    payload: Any, *, etf_code: str, fund_id: str,
    source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    code = _normalize_code(etf_code)
    if not isinstance(payload, dict) or payload.get("StatusCode") != 0:
        raise ValueError("安聯官方持股 API 回應失敗")
    entries = payload.get("Entries")
    if (not isinstance(entries, dict)
            or str(entries.get("FundID", "")).strip().upper() != fund_id):
        raise ValueError("安聯官方持股回傳 FundID 不符")
    data = entries.get("Data")
    asset = data.get("FundAsset") if isinstance(data, dict) else None
    tables = data.get("Table") if isinstance(data, dict) else None
    if not isinstance(asset, dict) or not isinstance(tables, list):
        raise ValueError("安聯官方持股尚無可用基金資產")
    stock_tables = [
        table for table in tables if isinstance(table, dict)
        and str(table.get("TableTitle", "")).startswith("股票 (")
    ]
    if len(stock_tables) != 1 or not isinstance(stock_tables[0].get("Rows"), list):
        raise ValueError("安聯官方持股缺少唯一股票權重表")
    rows = stock_tables[0]["Rows"]
    table = [["序號", "股票代號", "股票名稱", "股數", "權重(%)"], *rows]
    positions = _positions(
        table, code_index=1, name_index=2, weight_index=4, issuer="安聯"
    )
    title_match = re.fullmatch(
        r"股票 \((\d+(?:\.\d+)?)%\)",
        str(stock_tables[0].get("TableTitle", "")).strip(),
    )
    if title_match is None:
        raise ValueError("安聯官方持股缺少股票權重合計")
    declared_total = Decimal(title_match.group(1))
    parsed_total = sum(position["weight_pct"] for position in positions)
    if abs(parsed_total - declared_total) > Decimal("0.01"):
        raise ValueError("安聯官方持股與股票權重合計不符")
    return _snapshot(
        code, "安聯", "allianz_official_fund_assets", source_url,
        _parse_date(str(asset.get("NavDate", "")), "安聯"),
        positions, fetched_at,
    )


def fetch_hnh_constituent_snapshot(
    etf_code: str, *, timeout_seconds: float = 30,
    fetched_at: datetime | None = None,
) -> ETFConstituentSnapshotCreate:
    code = _normalize_code(etf_code)
    ssl_context = create_ssl_context(allow_legacy_x509=True)
    with httpx.Client(
        timeout=timeout_seconds, follow_redirects=True, verify=ssl_context,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    ) as client:
        origin_time = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        login = client.post(
            f"{HNH_API_BASE_URL}/Auth/SysLogin", json={},
            headers={
                "Accept-Language": "zh-TW",
                "Client_Id": HNH_PUBLIC_CLIENT_ID,
                "X-Origin-Time": origin_time,
            },
        )
        login.raise_for_status()
        _ensure_response_size(login, "華南永昌")
        token = parse_hnh_system_token(login.json())
        holdings_url = f"{HNH_API_BASE_URL}/Stk/PcfData"
        holdings = client.get(
            holdings_url, params={"ETFID": code},
            headers={
                "Accept-Language": "zh-TW",
                "Authorization": f"Bearer {token}",
                "X-Origin-Time": datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
            },
        )
        holdings.raise_for_status()
        _ensure_response_size(holdings, "華南永昌")
    return parse_hnh_constituent_payload(
        holdings.json(), etf_code=code,
        source_url=f"{holdings_url}?ETFID={code}",
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )


def fetch_allianz_constituent_snapshot(
    etf_code: str, *, timeout_seconds: float = 30,
    fetched_at: datetime | None = None,
) -> ETFConstituentSnapshotCreate:
    code = _normalize_code(etf_code)
    ssl_context = create_ssl_context(allow_legacy_x509=True)
    with httpx.Client(
        timeout=timeout_seconds, follow_redirects=True, verify=ssl_context,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    ) as client:
        antiforgery = client.get(
            f"{ALLIANZ_API_BASE_URL}/AntiForgery/GetAntiForgeryToken"
        )
        antiforgery.raise_for_status()
        _ensure_response_size(antiforgery, "安聯")
        antiforgery_payload = antiforgery.json()
        token = (
            str(antiforgery_payload.get("token", "")).strip()
            if isinstance(antiforgery_payload, dict) else ""
        )
        has_xsrf_cookie = any(
            cookie.name == "X-XSRF-TOKEN" for cookie in client.cookies.jar
        )
        if not token or not has_xsrf_cookie:
            raise ValueError("安聯官方 antiforgery session 回應失敗")
        request_headers = {"X-XSRF-TOKEN": token}
        catalog = client.post(
            f"{ALLIANZ_API_BASE_URL}/Fund/GetFundOverview",
            json={
                "Keyword": "", "FundNo": "", "FundType": -1,
                "PageSize": 999, "PageIndex": 1,
            },
            headers=request_headers,
        )
        catalog.raise_for_status()
        _ensure_response_size(catalog, "安聯")
        fund_id = parse_allianz_mapping(
            etf_code=code, catalog_payload=catalog.json()
        )
        holdings = client.post(
            f"{ALLIANZ_API_BASE_URL}/Fund/GetFundAssets",
            json={"FundID": fund_id}, headers=request_headers,
        )
        holdings.raise_for_status()
        _ensure_response_size(holdings, "安聯")
    return parse_allianz_constituent_payload(
        holdings.json(), etf_code=code, fund_id=fund_id,
        source_url=ALLIANZ_SOURCE_URL.format(fund_id=fund_id),
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )


SESSION_CONSTITUENT_FETCHERS: dict[
    str, Callable[..., ETFConstituentSnapshotCreate]
] = {
    "hnh": fetch_hnh_constituent_snapshot,
    "allianz": fetch_allianz_constituent_snapshot,
}
