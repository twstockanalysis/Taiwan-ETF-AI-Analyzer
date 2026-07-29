"""下載並檢查單檔 ETF 六個月市價報酬率。"""

import argparse
from datetime import date

from backend.app.data_sources.twse_stock_day import (
    fetch_price_history,
    save_price_history_snapshot,
)
from backend.app.services.performance_calculator import (
    InsufficientPriceHistoryError,
    calculate_six_month_price_return,
)


def build_argument_parser(
) -> argparse.ArgumentParser:
    """建立命令列參數。"""

    parser = argparse.ArgumentParser(
        description=(
            "計算單檔 ETF 六個月市價報酬率"
        )
    )

    parser.add_argument(
        "code",
        nargs="?",
        default="0050",
        help="ETF 證券代號",
    )

    parser.add_argument(
        "--months",
        type=int,
        default=8,
        help="下載月份數，預設為 8",
    )

    return parser


def main() -> None:
    """執行單檔 ETF 績效驗證。"""

    arguments = (
        build_argument_parser()
        .parse_args()
    )

    etf_code = (
        arguments.code.strip().upper()
    )

    print("開始下載 ETF 歷史價格")
    print(f"ETF 代號：{etf_code}")
    print(
        f"下載月份數：{arguments.months}"
    )

    records = fetch_price_history(
        etf_code=etf_code,
        end_date=date.today(),
        month_count=arguments.months,
    )

    snapshot = save_price_history_snapshot(
        etf_code=etf_code,
        records=records,
    )

    print("-" * 70)
    print(f"價格筆數：{len(records)}")
    print(f"原始快照：{snapshot.data_path}")

    if records:
        print(
            f"最早交易日："
            f"{records[0].trade_date}"
        )

        print(
            f"最新交易日："
            f"{records[-1].trade_date}"
        )

    try:
        result = (
            calculate_six_month_price_return(
                records
            )
        )

    except InsufficientPriceHistoryError as error:
        print("-" * 70)
        print(f"無法計算：{error}")
        return

    print("-" * 70)
    print("六個月市價報酬率計算成功")
    print(f"資料來源：{result.source_id}")
    print(f"績效期間：{result.period_code}")
    print(f"基準日：{result.as_of_date}")
    print(
        f"目標期初日："
        f"{result.target_start_date}"
    )
    print(
        f"實際期初日："
        f"{result.actual_start_date}"
    )
    print(f"期初收盤價：{result.start_close}")
    print(f"期末收盤價：{result.end_close}")
    print(
        f"六個月市價報酬率："
        f"{result.return_pct}%"
    )

    print("-" * 70)
    print(
        "注意：本結果未包含配息再投資，"
        "不是總報酬率。"
    )


if __name__ == "__main__":
    main()