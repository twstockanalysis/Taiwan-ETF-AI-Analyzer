"""顯示 ETF 六個月市價報酬率排行榜。"""

import argparse

from backend.app.repositories.performance_repository import (
    count_latest_performance_ranking,
    list_latest_performance_ranking,
)


def build_argument_parser(
) -> argparse.ArgumentParser:
    """建立命令列參數。"""

    parser = argparse.ArgumentParser(
        description=(
            "顯示 ETF 六個月市價報酬率排行榜"
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="顯示筆數，預設 20",
    )

    parser.add_argument(
        "--active",
        choices=(
            "all",
            "true",
            "false",
        ),
        default="all",
        help="主動式篩選",
    )

    parser.add_argument(
        "--include-bond",
        action="store_true",
        help="包含債券 ETF",
    )

    return parser


def main() -> None:
    """顯示最新績效排行榜。"""

    arguments = (
        build_argument_parser()
        .parse_args()
    )

    is_active: bool | None

    if arguments.active == "true":
        is_active = True

    elif arguments.active == "false":
        is_active = False

    else:
        is_active = None

    is_bond = (
        None
        if arguments.include_bond
        else False
    )

    rows = list_latest_performance_ranking(
        is_active=is_active,
        is_bond=is_bond,
        limit=arguments.limit,
    )

    total = count_latest_performance_ranking(
        is_active=is_active,
        is_bond=is_bond,
    )

    print("ETF 六個月市價報酬率排行榜")
    print(
        "注意：未包含配息再投資"
    )
    print("-" * 90)

    if not rows:
        print(
            "目前沒有六個月績效資料"
        )
        return

    for rank, row in enumerate(
        rows,
        start=1,
    ):
        management_type = (
            "主動式"
            if row["is_active"]
            else "被動式"
        )

        print(
            f"{rank:>3}. "
            f"{row['etf_code']:<8} "
            f"{row['name']:<24} "
            f"{management_type:<6} "
            f"{row['return_pct']:>10.4f}% "
            f"{row['as_of_date']}"
        )

    print("-" * 90)
    print(f"排行榜總數：{total}")

if __name__ == "__main__":
    main()