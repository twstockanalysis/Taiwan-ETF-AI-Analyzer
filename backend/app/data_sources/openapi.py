"""官方 OpenAPI 規格下載與分析工具。"""

import hashlib
import json
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from backend.app.config.settings import (
    RAW_DATA_DIR,
)
from backend.app.data_sources.registry import (
    DataSource,
    SourceType,
)


HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
}


@dataclass(
    frozen=True,
    slots=True,
)
class OpenAPISnapshot:
    """OpenAPI 規格快照結果。"""

    source_id: str
    downloaded_at: datetime
    document_path: Path
    metadata_path: Path
    checksum_sha256: str
    path_count: int


@dataclass(
    frozen=True,
    slots=True,
)
class EndpointCandidate:
    """符合搜尋條件的 API 端點。"""

    method: str
    path: str
    summary: str
    operation_id: str | None
    tags: tuple[str, ...]

def create_ssl_context(
    allow_legacy_x509: bool = False,
) -> ssl.SSLContext:
    """建立 HTTPS 憑證驗證環境。

    Args:
        allow_legacy_x509:
            是否停用 Python 3.13 的嚴格 X.509
            格式檢查。

    Returns:
        ssl.SSLContext:
            保留憑證及主機名稱驗證的 SSL Context。
    """

    context = ssl.create_default_context()

    if allow_legacy_x509:
        context.verify_flags &= (
            ~ssl.VERIFY_X509_STRICT
        )

    return context


def validate_openapi_document(
    document: object,
) -> dict[str, Any]:
    """確認下載內容為可分析的 OpenAPI 文件。

    Args:
        document: HTTP 回傳的 JSON 內容。

    Returns:
        dict[str, Any]: 驗證後的文件。

    Raises:
        ValueError: 文件格式不正確時拋出。
    """

    if not isinstance(document, dict):
        raise ValueError(
            "OpenAPI 規格最外層必須是 JSON 物件"
        )

    if (
        "swagger" not in document
        and "openapi" not in document
    ):
        raise ValueError(
            "文件缺少 swagger 或 openapi 版本欄位"
        )

    paths = document.get("paths")

    if not isinstance(paths, dict):
        raise ValueError(
            "OpenAPI 文件缺少有效的 paths"
        )

    return document


def fetch_openapi_document(
    specification_url: str,
    timeout_seconds: float = 30.0,
    allow_legacy_x509: bool = False,
) -> dict[str, Any]:
    """從官方網址下載 OpenAPI 規格。

    Args:
        specification_url:
            Swagger 或 OpenAPI JSON 網址。
        timeout_seconds:
            HTTP 逾時秒數。

    Returns:
        dict[str, Any]: OpenAPI JSON 文件。
    """
    ssl_context = create_ssl_context(
        allow_legacy_x509=allow_legacy_x509
    )

    response = httpx.get(
        specification_url,
        timeout=timeout_seconds,
        follow_redirects=True,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "TW-ETF-AI-Analyzer/0.1 "
                "(official-data-downloader)"
            ),
        },
    )

    response.raise_for_status()

    return validate_openapi_document(
        response.json()
    )


def calculate_sha256(
    content: bytes,
) -> str:
    """計算內容的 SHA-256。

    Args:
        content: 原始位元資料。

    Returns:
        str: 十六進位 SHA-256。
    """

    return hashlib.sha256(
        content
    ).hexdigest()


def save_openapi_snapshot(
    source: DataSource,
    document: dict[str, Any],
    output_root: Path | None = None,
    downloaded_at: datetime | None = None,
) -> OpenAPISnapshot:
    """儲存 OpenAPI 文件及中繼資料。

    Args:
        source: 資料來源設定。
        document: OpenAPI JSON 文件。
        output_root: 快照根目錄。
        downloaded_at: 指定下載時間，測試時使用。

    Returns:
        OpenAPISnapshot: 快照資訊。
    """

    if output_root is None:
        output_root = (
            RAW_DATA_DIR / "openapi"
        )

    if downloaded_at is None:
        downloaded_at = datetime.now(
            timezone.utc
        )

    timestamp = downloaded_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    source_directory = (
        output_root / source.source_id
    )

    source_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    document_text = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    document_bytes = document_text.encode(
        "utf-8"
    )

    checksum = calculate_sha256(
        document_bytes
    )

    document_path = (
        source_directory
        / f"{source.source_id}_{timestamp}.json"
    )

    metadata_path = (
        source_directory
        / f"{source.source_id}_{timestamp}.meta.json"
    )

    document_path.write_bytes(
        document_bytes
    )

    paths = document.get(
        "paths",
        {},
    )

    metadata = {
        "source_id": source.source_id,
        "display_name": source.display_name,
        "specification_url": (
            source.specification_url
        ),
        "downloaded_at": (
            downloaded_at.isoformat()
        ),
        "checksum_sha256": checksum,
        "path_count": len(paths),
        "document_path": str(
            document_path
        ),
    }

    metadata_text = json.dumps(
        metadata,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    metadata_path.write_text(
        metadata_text,
        encoding="utf-8",
    )

    # 另外保存 latest，方便後續程式直接讀取。
    latest_document_path = (
        source_directory / "latest.json"
    )

    latest_metadata_path = (
        source_directory / "latest.meta.json"
    )

    latest_document_path.write_bytes(
        document_bytes
    )

    latest_metadata_path.write_text(
        metadata_text,
        encoding="utf-8",
    )

    return OpenAPISnapshot(
        source_id=source.source_id,
        downloaded_at=downloaded_at,
        document_path=document_path,
        metadata_path=metadata_path,
        checksum_sha256=checksum,
        path_count=len(paths),
    )


def download_openapi_snapshot(
    source: DataSource,
    output_root: Path | None = None,
) -> tuple[
    dict[str, Any],
    OpenAPISnapshot,
]:
    """下載並儲存一個官方 OpenAPI 規格。

    Args:
        source: OpenAPI 資料來源。
        output_root: 快照根目錄。

    Returns:
        tuple:
            OpenAPI 文件及快照資訊。

    Raises:
        ValueError:
            來源不是 OpenAPI 或沒有規格網址。
    """

    if source.source_type != SourceType.OPEN_API:
        raise ValueError(
            f"資料來源不是 OpenAPI："
            f"{source.source_id}"
        )

    if not source.specification_url:
        raise ValueError(
            f"資料來源缺少規格網址："
            f"{source.source_id}"
        )

    document = fetch_openapi_document(
        specification_url=source.specification_url,
        allow_legacy_x509=(
            source.allow_legacy_x509
        ),
    )

    snapshot = save_openapi_snapshot(
        source=source,
        document=document,
        output_root=output_root,
    )

    return document, snapshot


def resolve_base_url(
    document: dict[str, Any],
) -> str | None:
    """從 OpenAPI 文件取得實際伺服器 Base URL。

    同時支援 Swagger 2 與 OpenAPI 3。

    Args:
        document: OpenAPI 文件。

    Returns:
        str | None: Base URL。
    """

    servers = document.get("servers")

    if (
        isinstance(servers, list)
        and servers
        and isinstance(servers[0], dict)
    ):
        server_url = servers[0].get("url")

        if isinstance(server_url, str):
            return server_url

    host = document.get("host")
    base_path = document.get(
        "basePath",
        "",
    )
    schemes = document.get("schemes")

    if (
        isinstance(host, str)
        and isinstance(schemes, list)
        and schemes
        and isinstance(schemes[0], str)
    ):
        return (
            f"{schemes[0]}://"
            f"{host}{base_path}"
        )

    return None


def find_endpoint_candidates(
    document: dict[str, Any],
    keywords: tuple[str, ...],
) -> list[EndpointCandidate]:
    """依關鍵字搜尋 OpenAPI 端點。

    搜尋範圍包括：
    路徑、摘要、說明、標籤及 operationId。

    Args:
        document: OpenAPI 文件。
        keywords: 搜尋關鍵字。

    Returns:
        list[EndpointCandidate]:
            符合條件的端點。
    """

    normalized_keywords = tuple(
        keyword.strip().lower()
        for keyword in keywords
        if keyword.strip()
    )

    candidates: list[EndpointCandidate] = []

    paths = document.get(
        "paths",
        {},
    )

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            normalized_method = method.lower()

            if normalized_method not in HTTP_METHODS:
                continue

            if not isinstance(operation, dict):
                continue

            summary = str(
                operation.get("summary", "")
            )

            description = str(
                operation.get("description", "")
            )

            operation_id_value = operation.get(
                "operationId"
            )

            operation_id = (
                str(operation_id_value)
                if operation_id_value
                else None
            )

            raw_tags = operation.get(
                "tags",
                [],
            )

            tags = tuple(
                str(tag)
                for tag in raw_tags
                if isinstance(tag, str)
            )

            searchable_text = " ".join(
                [
                    str(path),
                    summary,
                    description,
                    operation_id or "",
                    *tags,
                ]
            ).lower()

            if not any(
                keyword in searchable_text
                for keyword in normalized_keywords
            ):
                continue

            candidates.append(
                EndpointCandidate(
                    method=normalized_method.upper(),
                    path=str(path),
                    summary=summary,
                    operation_id=operation_id,
                    tags=tags,
                )
            )

    return sorted(
        candidates,
        key=lambda candidate: (
            candidate.path,
            candidate.method,
        ),
    )