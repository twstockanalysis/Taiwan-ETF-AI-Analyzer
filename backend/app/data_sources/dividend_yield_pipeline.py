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
) -> DividendYieldPipelineResult:
    """為尚無官方值的事件建立並保存回退殖利率。"""

    if request_interval_seconds < 0:
        raise ValueError(
            "request_interval_seconds 不得小於 0"
        )

    target_database_path = initialize_database(
        database_path
    )

    if price_fetcher is None:
        from backend.app.data_sources.twse_stock_day import (
            fetch_price_history,
        )

        price_fetcher = fetch_price_history

    candidates = list_dividend_yield_candidates(
        database_path=target_database_path,
        etf_code=etf_code,
        limit=limit,
    )

    resolved_today = today or date.today()

    records: list[
        ETFDividendSummaryMetricRecord
    ] = []

    failures: list[
        DividendYieldFailure
    ] = []

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

            price_records = price_fetcher(
                code,
                ex_dividend_date
                - timedelta(days=1),
                2,
                request_interval_seconds,
            )

            reference = (
                select_previous_trading_close(
                    records=price_records,
                    ex_dividend_date=(
                        ex_dividend_date
                    ),
                )
            )

            records.append(
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

        except Exception as error:
            failures.append(
                DividendYieldFailure(
                    dividend_id=dividend_id,
                    etf_code=code,
                    reason=str(error),
                )
            )

    import_summary = (
        upsert_dividend_summary_metrics(
            records=records,
            database_path=target_database_path,
        )
    )

    return DividendYieldPipelineResult(
        candidate_count=len(candidates),
        calculated_count=len(records),
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
