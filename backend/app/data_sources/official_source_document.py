"""官方正式配息來源文件下載與快照。"""

from __future__ import annotations

import hashlib
import json
import re
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from backend.app.config.settings import (
    RAW_DATA_DIR,
)
from backend.app.data_sources.actual_dividend_source_registry import (
    ActualDividendSource,
    SourceRetrievalPolicy,
)
from backend.app.data_sources.openapi import (
    create_ssl_context,
)


@dataclass(
    frozen=True,
    slots=True,
)
class OfficialHtmlSnapshot:
    """官方 HTML 文件快照。"""

    source_id: str
    source_document_id: str
    source_url: str
    downloaded_at: datetime
    data_path: Path
    metadata_path: Path
    checksum_sha256: str
    content_type: str


def normalize_hostname(
    value: str,
) -> str:
    """正規化網址主機名稱。"""

    return value.strip().lower().rstrip(".")


def validate_official_source_url(
    source: ActualDividendSource,
    source_url: str,
) -> str:
    """確認網址為來源 Registry 允許的 HTTPS 網域。"""

    parsed = urlparse(
        source_url.strip()
    )

    if parsed.scheme.lower() != "https":
        raise ValueError(
            "官方來源網址必須使用 HTTPS"
        )

    if not parsed.hostname:
        raise ValueError(
            "官方來源網址缺少主機名稱"
        )

    hostname = normalize_hostname(
        parsed.hostname
    )

    allowed_domains = {
        normalize_hostname(domain)
        for domain in source.official_domains
    }

    if hostname not in allowed_domains:
        raise ValueError(
            "官方來源網址不在允許網域："
            f"{hostname}"
        )

    return source_url.strip()


def build_safe_path_segment(
    value: str,
) -> str:
    """將來源文件 ID 轉成安全路徑片段。"""

    normalized = re.sub(
        r"[^0-9A-Za-z._-]+",
        "_",
        value.strip(),
    ).strip("._")

    if not normalized:
        raise ValueError(
            "source_document_id 無法建立安全路徑"
        )

    return normalized[:150]


def fetch_official_html(
    *,
    source: ActualDividendSource,
    source_url: str,
    timeout_seconds: float = 30.0,
    allow_network: bool = False,
    allow_legacy_x509: bool = False,
) -> tuple[str, str, str]:
    """明確允許後下載官方 HTML。

    Returns:
        tuple:
            HTML 文字、最終網址、Content-Type。
    """

    validated_url = (
        validate_official_source_url(
            source,
            source_url,
        )
    )

    if not allow_network:
        raise ValueError(
            "網路下載必須明確設定 "
            "allow_network=True"
        )

    if (
        source.retrieval_policy
        != SourceRetrievalPolicy.EXPLICIT_NETWORK
    ):
        raise ValueError(
            "此來源不允許程式下載"
        )

    ssl_context: ssl.SSLContext = (
        create_ssl_context(
            allow_legacy_x509=(
                allow_legacy_x509
            ),
        )
    )

    response = httpx.get(
        validated_url,
        timeout=timeout_seconds,
        follow_redirects=True,
        verify=ssl_context,
        headers={
            "Accept": (
                "text/html,"
                "application/xhtml+xml"
            ),
            "User-Agent": (
                "TW-ETF-AI-Analyzer/0.1 "
                "(official-document-downloader)"
            ),
        },
    )

    response.raise_for_status()

    final_url = str(
        response.url
    )

    validate_official_source_url(
        source,
        final_url,
    )

    content_type = (
        response.headers.get(
            "content-type",
            "text/html",
        )
        .split(";", 1)[0]
        .strip()
        .lower()
    )

    if content_type not in {
        "text/html",
        "application/xhtml+xml",
    }:
        raise ValueError(
            "官方來源回傳非 HTML 內容："
            f"{content_type}"
        )

    if not response.text.strip():
        raise ValueError(
            "官方來源文件內容為空白"
        )

    return (
        response.text,
        final_url,
        content_type,
    )


def save_official_html_snapshot(
    *,
    source: ActualDividendSource,
    source_document_id: str,
    source_url: str,
    html_text: str,
    output_root: Path | None = None,
    downloaded_at: datetime | None = None,
    content_type: str = "text/html",
) -> OfficialHtmlSnapshot:
    """以內容雜湊保存官方 HTML 與中繼資料。"""

    validated_url = (
        validate_official_source_url(
            source,
            source_url,
        )
    )

    if not html_text.strip():
        raise ValueError(
            "官方來源文件內容為空白"
        )

    if downloaded_at is None:
        downloaded_at = datetime.now(
            timezone.utc
        )

    if downloaded_at.tzinfo is None:
        raise ValueError(
            "downloaded_at 必須包含時區"
        )

    if output_root is None:
        output_root = (
            RAW_DATA_DIR
            / "dividends"
            / "source_documents"
        )

    normalized_document_id = (
        build_safe_path_segment(
            source_document_id
        )
    )

    document_bytes = html_text.encode(
        "utf-8"
    )

    checksum = hashlib.sha256(
        document_bytes
    ).hexdigest()

    document_directory = (
        output_root
        / source.source_id
        / normalized_document_id
    )

    document_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_path = (
        document_directory
        / f"{checksum}.html"
    )

    metadata_path = (
        document_directory
        / f"{checksum}.meta.json"
    )

    if not data_path.exists():
        data_path.write_bytes(
            document_bytes
        )

    metadata = {
        "schema_version": 1,
        "source_id": source.source_id,
        "source_document_id": (
            source_document_id
        ),
        "source_url": validated_url,
        "downloaded_at": (
            downloaded_at.isoformat()
        ),
        "content_type": content_type,
        "checksum_sha256": checksum,
        "data_path": str(data_path),
    }

    metadata_text = json.dumps(
        metadata,
        ensure_ascii=False,
        indent=2,
    )

    if not metadata_path.exists():
        metadata_path.write_text(
            metadata_text,
            encoding="utf-8",
        )

    (
        document_directory / "latest.html"
    ).write_bytes(
        document_bytes
    )

    (
        document_directory
        / "latest.meta.json"
    ).write_text(
        metadata_text,
        encoding="utf-8",
    )

    return OfficialHtmlSnapshot(
        source_id=source.source_id,
        source_document_id=(
            source_document_id
        ),
        source_url=validated_url,
        downloaded_at=downloaded_at,
        data_path=data_path,
        metadata_path=metadata_path,
        checksum_sha256=checksum,
        content_type=content_type,
    )


def capture_official_html_document(
    *,
    source: ActualDividendSource,
    source_document_id: str,
    source_url: str,
    html_text: str | None = None,
    output_root: Path | None = None,
    downloaded_at: datetime | None = None,
    allow_network: bool = False,
    timeout_seconds: float = 30.0,
) -> OfficialHtmlSnapshot:
    """取得並保存官方 HTML 文件。"""

    content_type = "text/html"
    resolved_url = source_url

    if html_text is None:
        (
            html_text,
            resolved_url,
            content_type,
        ) = fetch_official_html(
            source=source,
            source_url=source_url,
            timeout_seconds=(
                timeout_seconds
            ),
            allow_network=allow_network,
        )

    return save_official_html_snapshot(
        source=source,
        source_document_id=(
            source_document_id
        ),
        source_url=resolved_url,
        html_text=html_text,
        output_root=output_root,
        downloaded_at=downloaded_at,
        content_type=content_type,
    )
