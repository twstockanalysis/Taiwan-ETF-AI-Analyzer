"""中信投信 ETF 最新配息 PDF 候選探測。"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass

import httpx

from backend.app.data_sources.actual_dividend_source_registry import (
    SourceRetrievalPolicy,
    get_actual_dividend_source,
)
from backend.app.data_sources.openapi import create_ssl_context
from backend.app.data_sources.official_source_document import (
    validate_official_source_url,
)


SOURCE_ID = "ctbc_latest_etf_dividend_pdf"
DOCUMENT_URL_TEMPLATE = (
    "https://www.ctbcinvestments.com/fund/pdf/"
    "ETFLatestDividend/{etf_code}.pdf"
)
_ETF_CODE_PATTERN = re.compile(r"^[0-9A-Z]{4,10}$")


@dataclass(frozen=True, slots=True)
class CtbcDividendDocumentCandidate:
    """中信官方最新配息 PDF 候選。"""

    etf_code: str
    source_id: str
    document_id: str
    document_url: str
    content_type: str
    content_length: int | None
    information_basis: str = "UNKNOWN"


def normalize_ctbc_etf_code(etf_code: str) -> str:
    """正規化代號並阻擋路徑注入。"""

    normalized = etf_code.strip().upper()
    if not _ETF_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("ETF 代號格式錯誤")
    return normalized


def build_ctbc_latest_dividend_url(etf_code: str) -> str:
    """建立中信官方最新配息 PDF 網址。"""

    normalized = normalize_ctbc_etf_code(etf_code)
    url = DOCUMENT_URL_TEMPLATE.format(etf_code=normalized)
    validate_official_source_url(get_actual_dividend_source(SOURCE_ID), url)
    return url


def discover_ctbc_latest_dividend_document(
    *, etf_code: str, allow_network: bool = False,
    timeout_seconds: float = 30.0,
) -> CtbcDividendDocumentCandidate | None:
    """用 HEAD 探測官方 PDF，不下載或建立 ACTUAL。"""

    normalized = normalize_ctbc_etf_code(etf_code)
    source = get_actual_dividend_source(SOURCE_ID)
    if not allow_network:
        raise ValueError("網路探測必須明確設定 allow_network=True")
    if source.retrieval_policy != SourceRetrievalPolicy.EXPLICIT_NETWORK:
        raise ValueError("此來源不允許程式探測")

    response = httpx.head(
        build_ctbc_latest_dividend_url(normalized),
        timeout=timeout_seconds,
        follow_redirects=True,
        verify=create_ssl_context(),
        headers={
            "Accept": "application/pdf",
            "User-Agent": "TW-ETF-AI-Analyzer/0.1 (official-discovery)",
        },
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()

    final_url = str(response.url)
    validate_official_source_url(source, final_url)
    content_type = (
        response.headers.get("content-type", "")
        .split(";", 1)[0].strip().lower()
    )
    if content_type != "application/pdf":
        raise ValueError("中信最新配息路徑回傳非 PDF 內容")

    raw_length = response.headers.get("content-length")
    content_length = int(raw_length) if raw_length else None
    if content_length is not None and content_length <= 0:
        raise ValueError("中信最新配息 PDF 長度無效")

    return CtbcDividendDocumentCandidate(
        etf_code=normalized,
        source_id=SOURCE_ID,
        document_id=f"ctbc-latest-dividend-{normalized}",
        document_url=final_url,
        content_type=content_type,
        content_length=content_length,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    """建立中信官方 PDF 探測 CLI。"""

    parser = argparse.ArgumentParser(
        description="探測中信投信 ETF 最新配息官方 PDF"
    )
    parser.add_argument("--etf-code", required=True, help="ETF 證券代號")
    parser.add_argument(
        "--allow-network", action="store_true",
        help="明確允許對中信官方網址執行 HEAD 探測",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """輸出不下載 PDF 的候選中繼資料。"""

    arguments = build_argument_parser().parse_args(argv)
    if not arguments.allow_network:
        raise ValueError("自動探測必須明確指定 --allow-network")
    candidate = discover_ctbc_latest_dividend_document(
        etf_code=arguments.etf_code,
        allow_network=True,
    )
    payload = None
    if candidate is not None:
        payload = {
            "etf_code": candidate.etf_code,
            "source_id": candidate.source_id,
            "document_id": candidate.document_id,
            "document_url": candidate.document_url,
            "content_type": candidate.content_type,
            "content_length": candidate.content_length,
            "information_basis": candidate.information_basis,
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
