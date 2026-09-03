"""以除息前一交易日收盤價補齊單次配息殖利率。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Callable

from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.models.etf_analysis import (
    DividendYieldBasis,
    ETFDividendSummaryMetricRecord,
)
from backend.app.models.etf_price import (
    ETFDailyCloseRecord,
)
from backend.app.repositories.dividend_repository import (
    DividendSummaryMetricUpsertSummary,
    list_dividend_yield_candidates,
    upsert_dividend_summary_metrics,
)
from backend.app.repositories.daily_close_repository import (
    list_daily_closes,
    upsert_daily_close_records,
)
from backend.app.utils.date_tools import (
    list_month_starts,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DividendYieldFailure:
    """單筆回退殖利率無法建立的原因。"""

    dividend_id: int
    etf_code: str
    reason: str


@dataclass(
    frozen=True,
    slots=True,
)
class DividendYieldPipelineResult:
    """回退殖利率批次結果。"""

    candidate_count: int
    calculated_count: int
    failed_count: int
    import_summary: DividendSummaryMetricUpsertSummary
    failures: tuple[DividendYieldFailure, ...]


PriceFetcher = Callable[
    [str, date, int, float],
    list[ETFDailyCloseRecord],
]


PRICE_SOURCE_ID = "twse_stock_day"


def calculate_dividend_yield_pct(
    amount_per_unit: Decimal,
    reference_close_price: Decimal,
) -> Decimal:
    """計算單次現金股利殖利率百分比。"""

    if amount_per_unit < 0:
        raise ValueError(
            "每單位現金股利不得小於 0"
        )

    if reference_close_price <= 0:
        raise ValueError(
            "參考收盤價必須大於 0"
        )

    return (
        amount_per_unit
        / reference_close_price
        * Decimal("100")
    ).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP,
    )


def select_previous_trading_close(
    records: list[ETFDailyCloseRecord],
    ex_dividend_date: date,
) -> ETFDailyCloseRecord:
    """選出嚴格早於除息日的最近一筆收盤價。"""

    candidates = [
        record
        for record in records
        if record.trade_date
        < ex_dividend_date
    ]

    if not candidates:
        raise ValueError(
            "找不到除息日前的交易日收盤價"
        )

    return max(
        candidates,
        key=lambda record: record.trade_date,
    )


def run_dividend_yield_pipeline(
    database_path: str | Path | None = None,
    etf_code: str | None = None,
    limit: int | None = None,
    request_interval_seconds: float = 0.4,
    today: date | None = None,
    price_fetcher: PriceFetcher | None = None,
    prefer_cached_prices: bool = True,
    checkpoint_interval: int = 25,
) -> DividendYieldPipelineResult:
    """為尚無官方值的事件建立並保存回退殖利率。

    已保存的官方日收盤價優先於網路請求；快取沒有除息日前
    價格時才呼叫 price_fetcher。新下載價格立即保存，殖利率
    依 checkpoint_interval 分批提交，因此中斷後重跑會跳過
    已完成事件。這讓全市場績效與殖利率批次共用同一份
    TWSE facts，並保留完全相同的來源語意。
    """

    if request_interval_seconds < 0:
        raise ValueError(
            "request_interval_seconds 不得小於 0"
        )

    if checkpoint_interval < 1:
        raise ValueError(
            "checkpoint_interval 必須大於 0"
        )

    target_database_path = initialize_database(
        database_path
    )

    candidates = list_dividend_yield_candidates(
        database_path=target_database_path,
        etf_code=etf_code,
        limit=limit,
    )

    resolved_today = today or date.today()

    pending_records: list[
        ETFDividendSummaryMetricRecord
    ] = []

    calculated_count = 0
    inserted_count = 0
    updated_count = 0

    failures: list[
        DividendYieldFailure
    ] = []
    cached_prices_by_code: dict[
        str,
        list[ETFDailyCloseRecord],
    ] = {}

    for candidate in candidates:
        dividend_id = int(
            candidate["dividend_id"]
        )
        code = str(candidate["etf_code"])

        try:
            ex_dividend_date = date.fromisoformat(
                str(
                    candidate[
                        "ex_dividend_date"
                    ]
                )
            )

            if ex_dividend_date > resolved_today:
                raise ValueError(
                    "除息日尚未到達，不能建立正式回退值"
                )

            if str(
                candidate["currency"]
            ).upper() != "TWD":
                raise ValueError(
                    "非 TWD 配息不可使用 TWSE 收盤價回退"
                )

            price_end_date = (
                ex_dividend_date
                - timedelta(days=1)
            )
            price_month_starts = (
                list_month_starts(
                    end_date=price_end_date,
                    month_count=2,
                )
            )
            price_records = []

            if prefer_cached_prices:
                if code not in cached_prices_by_code:
                    cached_prices_by_code[code] = [
                        ETFDailyCloseRecord.model_validate(
                            row
                        )
                        for row in list_daily_closes(
                            code,
                            target_database_path,
                        )
                    ]

                price_records = [
                    row
                    for row in cached_prices_by_code[
                        code
                    ]
                    if row.trade_date
                    >= price_month_starts[0]
                    and row.trade_date
                    <= price_end_date
                ]

            if not price_records:
                if price_fetcher is None:
                    from backend.app.data_sources.twse_stock_day import (
                        fetch_price_history,
                    )

                    price_fetcher = (
                        fetch_price_history
                    )

                price_records = price_fetcher(
                    code,
                    price_end_date,
                    2,
                    request_interval_seconds,
                )

                upsert_daily_close_records(
                    records=price_records,
                    database_path=(
                        target_database_path
                    ),
                )

                cached = cached_prices_by_code.setdefault(
                    code,
                    [],
                )
                records_by_key = {
                    (
                        row.trade_date,
                        row.source_id,
                    ): row
                    for row in (
                        cached + price_records
                    )
                }
                cached_prices_by_code[code] = sorted(
                    records_by_key.values(),
                    key=lambda row: row.trade_date,
                )

            reference = (
                select_previous_trading_close(
                    records=price_records,
                    ex_dividend_date=(
                        ex_dividend_date
                    ),
                )
            )

            pending_records.append(
                ETFDividendSummaryMetricRecord(
                    dividend_id=dividend_id,
                    yield_pct=(
                        calculate_dividend_yield_pct(
                            amount_per_unit=Decimal(
                                str(
                                    candidate[
                                        "amount_per_unit"
                                    ]
                                )
                            ),
                            reference_close_price=(
                                reference.close_price
                            ),
                        )
                    ),
                    yield_basis=(
                        DividendYieldBasis.CALCULATED
                    ),
                    yield_source_id=(
                        PRICE_SOURCE_ID
                    ),
                    reference_trade_date=(
                        reference.trade_date
                    ),
                    reference_close_price=(
                        reference.close_price
                    ),
                )
            )
            calculated_count += 1

            if (
                len(pending_records)
                >= checkpoint_interval
            ):
                checkpoint_summary = (
                    upsert_dividend_summary_metrics(
                        records=pending_records,
                        database_path=(
                            target_database_path
                        ),
                    )
                )
                inserted_count += (
                    checkpoint_summary
                    .inserted_records
                )
                updated_count += (
                    checkpoint_summary
                    .updated_records
                )
                pending_records.clear()

        except Exception as error:
            failures.append(
                DividendYieldFailure(
                    dividend_id=dividend_id,
                    etf_code=code,
                    reason=str(error),
                )
            )

    final_summary = (
        upsert_dividend_summary_metrics(
            records=pending_records,
            database_path=target_database_path,
        )
    )

    inserted_count += final_summary.inserted_records
    updated_count += final_summary.updated_records

    import_summary = (
        DividendSummaryMetricUpsertSummary(
            total_records=calculated_count,
            inserted_records=inserted_count,
            updated_records=updated_count,
        )
    )

    return DividendYieldPipelineResult(
        candidate_count=len(candidates),
        calculated_count=calculated_count,
        failed_count=len(failures),
        import_summary=import_summary,
        failures=tuple(failures),
    )


def parse_arguments() -> argparse.Namespace:
    """解析 CLI 參數。"""

    parser = argparse.ArgumentParser(
        description=(
            "補齊 ETF 單次配息殖利率；"
            "官方值已存在時不覆蓋。"
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--code",
        default=None,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=0.4,
    )

    return parser.parse_args()


def main() -> None:
    """執行回退殖利率 Pipeline。"""

    arguments = parse_arguments()

    result = run_dividend_yield_pipeline(
        database_path=arguments.database,
        etf_code=arguments.code,
        limit=arguments.limit,
        request_interval_seconds=(
            arguments.request_interval_seconds
        ),
    )

    print(
        "殖利率候選："
        f"{result.candidate_count}"
    )
    print(
        "計算成功："
        f"{result.calculated_count}"
    )
    print(
        "失敗："
        f"{result.failed_count}"
    )

    for failure in result.failures:
        print(
            "- "
            f"{failure.etf_code} / "
            f"dividend_id={failure.dividend_id}: "
            f"{failure.reason}"
        )


if __name__ == "__main__":
    main()
