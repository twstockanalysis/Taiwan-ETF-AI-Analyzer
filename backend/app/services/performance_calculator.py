"""ETF 市價報酬率計算服務。"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from backend.app.models.etf_price import (
    ETFDailyCloseRecord,
)
from backend.app.utils.date_tools import (
    shift_months,
)


class InsufficientPriceHistoryError(
    ValueError
):
    """ETF 沒有足夠價格歷史。"""


@dataclass(
    frozen=True,
    slots=True,
)
class PriceReturnResult:
    """ETF 期間市價報酬率結果。"""

    etf_code: str
    period_code: str
    as_of_date: date
    target_start_date: date
    actual_start_date: date
    start_close: Decimal
    end_close: Decimal
    return_pct: Decimal
    source_id: str


def calculate_six_month_price_return(
    records: list[ETFDailyCloseRecord],
    maximum_start_gap_days: int = 14,
) -> PriceReturnResult:
    """計算 ETF 六個月市價報酬率。

    期初價格使用目標日期當日或其後
    第一個交易日的收盤價。

    Args:
        records:
            依交易日期取得的收盤價。
        maximum_start_gap_days:
            目標期初日與實際交易日允許差距。

    Returns:
        PriceReturnResult:
            六個月市價報酬率。

    Raises:
        InsufficientPriceHistoryError:
            資料不足六個月。
        ValueError:
            資料內容不一致。
    """

    if not records:
        raise InsufficientPriceHistoryError(
            "沒有可計算的價格資料"
        )

    records_by_date = {
        record.trade_date: record
        for record in records
    }

    ordered_records = sorted(
        records_by_date.values(),
        key=lambda record: (
            record.trade_date
        ),
    )

    etf_codes = {
        record.etf_code
        for record in ordered_records
    }

    if len(etf_codes) != 1:
        raise ValueError(
            "價格資料包含多個 ETF 代號"
        )

    source_ids = {
        record.source_id
        for record in ordered_records
    }

    if len(source_ids) != 1:
        raise ValueError(
            "價格資料包含多個資料來源"
        )

    end_record = ordered_records[-1]

    target_start_date = shift_months(
        end_record.trade_date,
        -6,
    )

    start_candidates = [
        record
        for record in ordered_records
        if record.trade_date
        >= target_start_date
    ]

    if not start_candidates:
        raise InsufficientPriceHistoryError(
            "找不到六個月前的期初價格"
        )

    start_record = start_candidates[0]

    maximum_start_date = (
        target_start_date
        + timedelta(
            days=maximum_start_gap_days
        )
    )

    if (
        start_record.trade_date
        > maximum_start_date
    ):
        raise InsufficientPriceHistoryError(
            "ETF 上市時間或價格歷史不足六個月"
        )

    return_pct = (
        (
            end_record.close_price
            / start_record.close_price
            - Decimal("1")
        )
        * Decimal("100")
    ).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP,
    )

    return PriceReturnResult(
        etf_code=end_record.etf_code,
        period_code="6M",
        as_of_date=end_record.trade_date,
        target_start_date=(
            target_start_date
        ),
        actual_start_date=(
            start_record.trade_date
        ),
        start_close=(
            start_record.close_price
        ),
        end_close=(
            end_record.close_price
        ),
        return_pct=return_pct,
        source_id=end_record.source_id,
    )