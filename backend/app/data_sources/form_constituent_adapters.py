"""以官方 HTML 表單查詢的 ETF 成分股來源。"""

import re
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urljoin, urlparse

import httpx

from backend.app.data_sources.direct_constituent_adapters import (
    USER_AGENT,
    _normalize_code,
    _parse_date,
    _positions,
    _snapshot,
    _stock_table,
    _TableParser,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.models.etf_constituent import ETFConstituentSnapshotCreate


UNION_BUYBACK_URL = "https://www.usitc.com.tw/CustCenter/BuyBackList"
MAX_RESPONSE_BYTES = 5_000_000


def _ensure_union_response(response: httpx.Response) -> None:
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("聯邦官方成分股回應超過容量上限")
    if "text/html" not in response.headers.get("content-type", "").lower():
        raise ValueError("聯邦官方成分股回應不是 HTML")


def parse_union_form_contract(content: str) -> tuple[frozenset[str], str]:
    form_match = re.search(
        r'<form\b(?=[^>]*\baction=["\']?/CustCenter/BuyBackList["\']?)'
        r'(?=[^>]*\bmethod=["\']?post["\']?)[^>]*>(.*?)</form>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if form_match is None:
        raise ValueError("聯邦官方申購買回表單契約已變更")
    form = form_match.group(1)
    select_match = re.search(
        r'<select\b[^>]*\bname=["\']?FundNo["\']?[^>]*>(.*?)</select>',
        form,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if select_match is None:
        raise ValueError("聯邦官方申購買回表單缺少基金清單")
    codes = frozenset(
        match.upper() for match in re.findall(
            r'<option\b[^>]*\bvalue=["\']?([0-9A-Z]{4,10})["\']?',
            select_match.group(1), flags=re.IGNORECASE,
        )
    )
    date_match = re.search(
        r'<input\b(?=[^>]*\bname=["\']?sDate["\']?)'
        r'[^>]*\bvalue=["\'](20\d{2}-\d{2}-\d{2})["\']',
        form,
        flags=re.IGNORECASE,
    )
    if not codes or date_match is None:
        raise ValueError("聯邦官方申購買回表單缺少基金或日期欄位")
    return codes, date_match.group(1)


def resolve_union_query_date(content: str, *, etf_code: str) -> str:
    code = _normalize_code(etf_code)
    codes, query_date = parse_union_form_contract(content)
    if code not in codes:
        raise ValueError(f"聯邦官方申購買回表單找不到 ETF：{code}")
    return query_date


def parse_union_constituent_html(
    content: str, *, etf_code: str, source_url: str, fetched_at: datetime,
) -> ETFConstituentSnapshotCreate:
    code = _normalize_code(etf_code)
    identity_match = re.search(
        r"<h2[^>]*>.*?\(\s*([0-9A-Z]{4,10})\s*\).*?</h2>",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if identity_match is None or identity_match.group(1).upper() != code:
        raise ValueError(f"聯邦官方成分股回應與要求的 {code} 不符")
    date_match = re.search(
        r"資料日期\s*[：:]\s*(20\d{2}-\d{1,2}-\d{1,2})", content
    )
    parser = _TableParser()
    parser.feed(content)
    table = _stock_table(
        parser.tables, ("股票代號", "股票名稱", "權重(%)"), "聯邦"
    )
    return _snapshot(
        code, "聯邦", "union_official_buyback_holdings", source_url,
        _parse_date(date_match.group(1) if date_match else "", "聯邦"),
        _positions(
            table, code_index=0, name_index=1, weight_index=3, issuer="聯邦"
        ),
        fetched_at,
    )


def fetch_union_constituent_snapshot(
    etf_code: str, *, timeout_seconds: float = 30,
    fetched_at: datetime | None = None,
) -> ETFConstituentSnapshotCreate:
    code = _normalize_code(etf_code)
    ssl_context = create_ssl_context(allow_legacy_x509=True)
    with httpx.Client(
        timeout=timeout_seconds, follow_redirects=True, verify=ssl_context,
        headers={"Accept": "text/html", "User-Agent": USER_AGENT},
    ) as client:
        form_response = client.get(UNION_BUYBACK_URL)
        form_response.raise_for_status()
        _ensure_union_response(form_response)
        query_date = resolve_union_query_date(
            form_response.text, etf_code=code
        )
        holdings_response = client.post(
            UNION_BUYBACK_URL, data={"FundNo": code, "sDate": query_date}
        )
        holdings_response.raise_for_status()
        _ensure_union_response(holdings_response)
        if urlparse(str(holdings_response.url)).netloc.lower() != "www.usitc.com.tw":
            raise ValueError("聯邦官方成分股回應離開允許網域")
    return parse_union_constituent_html(
        holdings_response.text, etf_code=code,
        source_url=urljoin(UNION_BUYBACK_URL, "/CustCenter/BuyBackList"),
        fetched_at=fetched_at or datetime.now(timezone.utc),
    )


FORM_CONSTITUENT_FETCHERS: dict[
    str, Callable[..., ETFConstituentSnapshotCreate]
] = {"union": fetch_union_constituent_snapshot}
