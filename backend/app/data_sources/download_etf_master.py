"""下載 TWSE 官方 ETF 主資料。"""

from typing import Any

from backend.app.data_sources.api_client import (
    fetch_json_records,
)
from backend.app.data_sources.endpoints import (
    build_endpoint_url,
    get_api_endpoint,
)
from backend.app.data_sources.raw_snapshot import (
    save_json_records_snapshot,
)


ENDPOINT_ID = "twse_fund_master"


def display_record_sample(
    records: list[dict[str, Any]],
) -> None:
    """顯示資料欄位及前幾筆內容。

    Args:
        records:
            官方 API 資料紀錄。
    """

    if not records:
        print("官方 API 回傳 0 筆資料")
        return

    first_record = records[0]

    print("第一筆資料的欄位")
    print("-" * 70)

    for key in first_record:
        print(key)

    print("-" * 70)
    print("前 3 筆資料摘要")

    for record in records[:3]:
        print(
            {
                "基金代號": record.get(
                    "基金代號"
                ),
                "基金簡稱": record.get(
                    "基金簡稱"
                ),
                "基金類型": record.get(
                    "基金類型"
                ),
                "成立日期": record.get(
                    "成立日期"
                ),
                "上市日期": record.get(
                    "上市日期"
                ),
            }
        )


def main() -> None:
    """下載並保存官方 ETF 主資料。"""

    endpoint = get_api_endpoint(
        ENDPOINT_ID
    )

    print("開始下載官方 ETF 主資料")
    print(f"Endpoint ID：{endpoint.endpoint_id}")
    print(
        f"API URL："
        f"{build_endpoint_url(endpoint)}"
    )

    records = fetch_json_records(
        endpoint
    )

    snapshot = save_json_records_snapshot(
        endpoint=endpoint,
        records=records,
    )

    print("官方 ETF 主資料下載成功")
    print(f"資料筆數：{snapshot.record_count}")
    print(f"資料快照：{snapshot.data_path}")
    print(
        f"中繼資料："
        f"{snapshot.metadata_path}"
    )
    print(
        f"SHA-256："
        f"{snapshot.checksum_sha256}"
    )

    display_record_sample(
        records
    )


if __name__ == "__main__":
    main()