"""將 TWSE ETF 原始資料正規化。"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    REJECTED_DATA_DIR,
)
from backend.app.data_sources.normalizers.twse_fund_master import (
    normalize_twse_fund_records,
)


ENDPOINT_ID = "twse_fund_master"

RAW_FILE_PATH = (
    RAW_DATA_DIR
    / "etf_master"
    / ENDPOINT_ID
    / "latest.json"
)


def load_raw_records(
    file_path: Path,
) -> list[dict[str, Any]]:
    """讀取官方原始 JSON。"""

    if not file_path.exists():
        raise FileNotFoundError(
            f"找不到原始資料：{file_path}"
        )

    payload = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(payload, list):
        raise ValueError(
            "原始資料最外層必須是 JSON 陣列"
        )

    records: list[dict[str, Any]] = []

    for index, item in enumerate(
        payload,
        start=1,
    ):
        if not isinstance(item, dict):
            raise ValueError(
                f"第 {index} 筆不是 JSON 物件"
            )

        records.append(item)

    return records


def write_json(
    file_path: Path,
    payload: object,
) -> None:
    """將資料以 UTF-8 JSON 格式寫入。"""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    """執行 ETF 主資料正規化。"""

    print("開始正規化 ETF 主資料")
    print(f"原始資料：{RAW_FILE_PATH}")

    records = load_raw_records(
        RAW_FILE_PATH
    )

    result = normalize_twse_fund_records(
        records
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    processed_directory = (
        PROCESSED_DATA_DIR
        / "etf_master"
        / ENDPOINT_ID
    )

    rejected_directory = (
        REJECTED_DATA_DIR
        / "etf_master"
        / ENDPOINT_ID
    )

    accepted_payload = [
        record.model_dump(
            mode="json"
        )
        for record in result.accepted
    ]

    rejected_payload = [
        {
            "index": item.index,
            "reason": item.reason,
            "record": item.record,
        }
        for item in result.rejected
    ]

    processed_snapshot_path = (
        processed_directory
        / (
            f"{ENDPOINT_ID}_"
            f"{timestamp}.json"
        )
    )

    rejected_snapshot_path = (
        rejected_directory
        / (
            f"{ENDPOINT_ID}_"
            f"{timestamp}.json"
        )
    )

    write_json(
        processed_snapshot_path,
        accepted_payload,
    )

    write_json(
        processed_directory / "latest.json",
        accepted_payload,
    )

    write_json(
        rejected_snapshot_path,
        rejected_payload,
    )

    write_json(
        rejected_directory / "latest.json",
        rejected_payload,
    )

    print("-" * 70)
    print(f"原始筆數：{len(records)}")
    print(
        f"接受筆數："
        f"{len(result.accepted)}"
    )
    print(
        f"拒絕筆數："
        f"{len(result.rejected)}"
    )
    print(
        f"正規化資料："
        f"{processed_snapshot_path}"
    )
    print(
        f"拒絕資料："
        f"{rejected_snapshot_path}"
    )

    print("-" * 70)
    print("前 5 筆正規化 ETF")

    for record in result.accepted[:5]:
        print(
            {
                "code": record.code,
                "name": record.name,
                "is_active": (
                    record.is_active
                ),
                "is_bond": (
                    record.is_bond
                ),
                "listing_date": (
                    record.listing_date
                ),
            }
        )

    print("-" * 70)
    print("前 5 筆拒絕原因")

    for rejected in result.rejected[:5]:
        print(
            {
                "index": rejected.index,
                "reason": rejected.reason,
            }
        )


if __name__ == "__main__":
    main()