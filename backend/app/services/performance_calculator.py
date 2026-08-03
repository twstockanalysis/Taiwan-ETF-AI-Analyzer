"""ETF 市價報酬率計算服務。"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from backend.app.models.etf_analysis import (
    PerformanceMetric,
    PerformancePeriod,
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


class UnsupportedPerformancePeriodError(
    ValueError
):
    """目前市價報酬率不支援指定期間。"""


SUPPORTED_PRICE_RETURN_MONTHS = {
    PerformancePeriod.ONE_MONTH: 1,
    PerformancePeriod.THREE_MONTHS: 3,
    PerformancePeriod.SIX_MONTHS: 6,
    PerformancePeriod.ONE_YEAR: 12,
}


@dataclass(
    frozen=True,
    slots=True,
)
class PriceReturnResult:
    """ETF 期間市價報酬率結果。"""

    etf_code: str
    period_code: PerformancePeriod
    metric_code: PerformanceMetric
    as_of_date: date
    target_start_date: date
    actual_start_date: date
    start_close: Decimal
    end_close: Decimal
    return_pct: Decimal
    source_id: str


def normalize_price_return_period(
    period_code: PerformancePeriod | str,
) -> PerformancePeriod:
    """驗證並正規化績效期間。"""

    try:
        normalized_period = (
            PerformancePeriod(
                period_code
            )
        )

    except ValueError as error:
        raise UnsupportedPerformancePeriodError(
            f"未知績效期間：{period_code}"
        ) from error

    if (
        normalized_period
        not in SUPPORTED_PRICE_RETURN_MONTHS
    ):
        raise UnsupportedPerformancePeriodError(
            "目前市價報酬率只支援："
            "1M、3M、6M、1Y"
        )

    return normalized_period


def calculate_price_return(
    records: list[ETFDailyCloseRecord],
    period_code: PerformancePeriod | str,
    maximum_start_gap_days: int = 14,
) -> PriceReturnResult:
    """計算指定期間的 ETF 市價報酬率。

    期末價格使用資料中最新交易日。

    期初價格使用目標日期當日或其後
    第一個可取得的交易日。

    Args:
        records:
            ETF 每日收盤價。
        period_code:
            1M、3M、6M 或 1Y。
        maximum_start_gap_days:
            目標期初日與實際交易日的
            最大容許差距。

    Returns:
        PriceReturnResult:
            市價報酬率結果。

    Raises:
        InsufficientPriceHistoryError:
            價格歷史不足。
        UnsupportedPerformancePeriodError:
            期間目前不支援。
        ValueError:
            資料包含多個 ETF 或來源。
    """

    if maximum_start_gap_days < 0:
        raise ValueError(
            "maximum_start_gap_days "
            "不得小於 0"
        )

    normalized_period = (
        normalize_price_return_period(
            period_code
        )
    )

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

    period_months = (
        SUPPORTED_PRICE_RETURN_MONTHS[
            normalized_period
        ]
    )

    target_start_date = shift_months(
        end_record.trade_date,
        -period_months,
    )

    start_candidates = [
        record
        for record in ordered_records
        if record.trade_date
        >= target_start_date
    ]

    if not start_candidates:
        raise InsufficientPriceHistoryError(
            f"找不到 {normalized_period.value} "
            "所需的期初價格"
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
            f"ETF 價格歷史不足 "
            f"{normalized_period.value}"
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
        period_code=normalized_period,
        metric_code=(
            PerformanceMetric.PRICE_RETURN
        ),
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


def calculate_six_month_price_return(
    records: list[ETFDailyCloseRecord],
    maximum_start_gap_days: int = 14,
) -> PriceReturnResult:
    """保留原六個月計算函式的相容介面。"""

    return calculate_price_return(
        records=records,
        period_code=(
            PerformancePeriod.SIX_MONTHS
        ),
        maximum_start_gap_days=(
            maximum_start_gap_days
        ),
    )