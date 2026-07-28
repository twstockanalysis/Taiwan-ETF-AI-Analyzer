"""顯示最新 ETF 匯入批次。"""

from backend.app.repositories.import_batch_repository import (
    get_latest_import_batch,
)


def main() -> None:
    """顯示最新匯入結果。"""

    batch = get_latest_import_batch()

    if batch is None:
        print("目前沒有匯入批次紀錄")
        return

    print("最新 ETF 匯入批次")
    print("-" * 70)

    fields = (
        "id",
        "pipeline_name",
        "source_id",
        "endpoint_id",
        "started_at",
        "completed_at",
        "status",
        "raw_record_count",
        "accepted_record_count",
        "rejected_record_count",
        "inserted_record_count",
        "updated_record_count",
        "deleted_development_record_count",
        "quality_report_path",
        "error_message",
    )

    for field in fields:
        print(
            f"{field}：{batch[field]}"
        )


if __name__ == "__main__":
    main()