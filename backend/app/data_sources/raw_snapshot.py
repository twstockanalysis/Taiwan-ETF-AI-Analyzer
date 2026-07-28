"""官方原始資料快照儲存模組。"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import (
    RAW_DATA_DIR,
)
from backend.app.data_sources.endpoints import (
    ApiEndpoint,
    build_endpoint_url,
)


@dataclass(
    frozen=True,
    slots=True,
)
class RawDataSnapshot:
    """官方原始資料快照結果。"""

    endpoint_id: str
    downloaded_at: datetime
    data_path: Path
    metadata_path: Path
    checksum_sha256: str
    record_count: int


def calculate_sha256(
    content: bytes,
) -> str:
    """計算資料的 SHA-256。

    Args:
        content:
            原始位元資料。

    Returns:
        str:
            SHA-256 十六進位字串。
    """

    return hashlib.sha256(
        content
    ).hexdigest()


def save_json_records_snapshot(
    endpoint: ApiEndpoint,
    records: list[dict[str, Any]],
    output_root: Path | None = None,
    downloaded_at: datetime | None = None,
) -> RawDataSnapshot:
    """保存官方 JSON 資料與中繼資訊。

    Args:
        endpoint:
            API Endpoint 設定。
        records:
            官方 JSON 資料紀錄。
        output_root:
            指定快照根目錄。
        downloaded_at:
            指定下載時間，測試時使用。

    Returns:
        RawDataSnapshot:
            快照檔案資訊。
    """

    if output_root is None:
        output_root = (
            RAW_DATA_DIR
            / endpoint.dataset_kind.value
        )

    if downloaded_at is None:
        downloaded_at = datetime.now(
            timezone.utc
        )

    timestamp = downloaded_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    endpoint_directory = (
        output_root / endpoint.endpoint_id
    )

    endpoint_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_text = json.dumps(
        records,
        ensure_ascii=False,
        indent=2,
    )

    data_bytes = data_text.encode(
        "utf-8"
    )

    checksum = calculate_sha256(
        data_bytes
    )

    data_path = (
        endpoint_directory
        / (
            f"{endpoint.endpoint_id}_"
            f"{timestamp}.json"
        )
    )

    metadata_path = (
        endpoint_directory
        / (
            f"{endpoint.endpoint_id}_"
            f"{timestamp}.meta.json"
        )
    )

    data_path.write_bytes(
        data_bytes
    )

    first_record_keys: list[str] = []

    if records:
        first_record_keys = list(
            records[0].keys()
        )

    metadata = {
        "endpoint_id": endpoint.endpoint_id,
        "display_name": endpoint.display_name,
        "source_id": endpoint.source_id,
        "dataset_kind": (
            endpoint.dataset_kind.value
        ),
        "endpoint_url": build_endpoint_url(
            endpoint
        ),
        "downloaded_at": (
            downloaded_at.isoformat()
        ),
        "record_count": len(records),
        "checksum_sha256": checksum,
        "first_record_keys": (
            first_record_keys
        ),
        "data_path": str(data_path),
    }

    metadata_text = json.dumps(
        metadata,
        ensure_ascii=False,
        indent=2,
    )

    metadata_path.write_text(
        metadata_text,
        encoding="utf-8",
    )

    latest_data_path = (
        endpoint_directory / "latest.json"
    )

    latest_metadata_path = (
        endpoint_directory
        / "latest.meta.json"
    )

    latest_data_path.write_bytes(
        data_bytes
    )

    latest_metadata_path.write_text(
        metadata_text,
        encoding="utf-8",
    )

    return RawDataSnapshot(
        endpoint_id=endpoint.endpoint_id,
        downloaded_at=downloaded_at,
        data_path=data_path,
        metadata_path=metadata_path,
        checksum_sha256=checksum,
        record_count=len(records),
    )