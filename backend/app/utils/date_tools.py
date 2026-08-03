"""日期計算共用工具。"""

from calendar import monthrange
from datetime import date


def shift_months(
    value: date,
    months: int,
) -> date:
    """將日期向前或向後移動指定月數。

    月底日期若超出目標月份天數，
    會自動調整為目標月份最後一天。

    Args:
        value:
            原始日期。
        months:
            月份位移；負數代表向前。

    Returns:
        date:
            位移後日期。
    """

    month_index = (
        value.year * 12
        + value.month
        - 1
        + months
    )

    target_year, target_month_index = divmod(
        month_index,
        12,
    )

    target_month = target_month_index + 1

    target_day = min(
        value.day,
        monthrange(
            target_year,
            target_month,
        )[1],
    )

    return date(
        target_year,
        target_month,
        target_day,
    )


def list_month_starts(
    end_date: date,
    month_count: int,
) -> list[date]:
    """取得截至指定日期的月份起始日。

    Args:
        end_date:
            最後一個月份所屬日期。
        month_count:
            要取得的月份數量。

    Returns:
        list[date]:
            由舊到新排序的每月一日。

    Raises:
        ValueError:
            月份數量小於 1。
    """

    if month_count < 1:
        raise ValueError(
            "month_count 必須大於 0"
        )

    current_month = date(
        end_date.year,
        end_date.month,
        1,
    )

    return [
        shift_months(
            current_month,
            -offset,
        )
        for offset in reversed(
            range(month_count)
        )
    ]