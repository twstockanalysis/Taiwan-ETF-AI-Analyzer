"""將正規化 ETF 主資料匯入 SQLite。"""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.models.etf_import import (
    ETFImportRecord,
)
from backend.app.repositories.etf_import_repository import (
    ETFImportSummary,
    upsert_etf_master,
)


ENDPOINT_ID = "twse_fund_master"

PROCESSED_FILE_PATH = (
    PROCESSED_DATA_DIR
    / "etf_master"
    / ENDPOINT_ID
    / "latest.json"
)


def load_processed_records(
    file_path: Path,
) -> list[ETFImportRecord]:
    """讀取並驗證正規化 ETF 資料。

    Args:
        file_path:
            processed JSON 檔案路徑。

    Returns:
        list[ETFImportRecord]:
            驗證完成的 ETF 資料。

    Raises:
        FileNotFoundError:
            找不到 processed 檔案。
        ValueError:
            JSON 格式或紀錄內容不合法。
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"找不到正規化資料：{file_path}"
        )

    payload: Any = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(payload, list):
        raise ValueError(
            "正規化資料最外層必須是 JSON 陣列"
        )

    records: list[ETFImportRecord] = []

    for index, item in enumerate(
        payload,
        start=1,
    ):
        if not isinstance(item, dict):
            raise ValueError(
                f"第 {index} 筆資料不是 JSON 物件"
            )

        try:
            record = (
                ETFImportRecord.model_validate(
                    item
                )
            )

        except ValidationError as error:
            raise ValueError(
                f"第 {index} 筆 ETF 資料驗證失敗："
                f"{error}"
            ) from error

        records.append(record)

    return records


def display_summary(
    summary: ETFImportSummary,
) -> None:
    """顯示 ETF 匯入結果。"""

    print("-" * 70)
    print(
        f"處理筆數："
        f"{summary.total_records}"
    )
    print(
        f"新增筆數："
        f"{summary.inserted_records}"
    )
    print(
        f"更新筆數："
        f"{summary.updated_records}"
    )
    print(
        "刪除開發測試資料："
        f"{summary.deleted_development_records}"
    )


def main() -> None:
    """執行 ETF 主資料匯入。"""

    print("開始匯入 ETF 主資料")
    print(
        f"正規化資料："
        f"{PROCESSED_FILE_PATH}"
    )

    records = load_processed_records(
        PROCESSED_FILE_PATH
    )

    database_path = initialize_database()

    summary = upsert_etf_master(
        records=records,
        database_path=database_path,
        remove_development_records=True,
    )

    print("ETF 主資料匯入成功")

    display_summary(
        summary
    )


if __name__ == "__main__":
    main()