"""ETF 多期間市價報酬率批次 Pipeline。"""

import argparse
import json
import time
from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
    REJECTED_DATA_DIR,
)
from backend.app.data_sources.twse_stock_day import (
    fetch_price_history,
    save_price_history_snapshot,
)
from backend.app.models.etf_analysis import (
    ETFPerformanceImportRecord,
    PerformanceMetric,
    PerformancePeriod,
)
from backend.app.repositories.performance_repository import (
    PerformanceUpsertSummary,
    list_performance_candidates,
    upsert_performance_records,
)
from backend.app.repositories.daily_close_repository import (
    upsert_daily_close_records,
)
from backend.app.services.performance_calculator import (
    InsufficientPriceHistoryError,
    calculate_price_return,
    normalize_price_return_period,
)


SOURCE_ID = "twse_stock_day"

DEFAULT_PERIODS = (
    PerformancePeriod.ONE_MONTH,
    PerformancePeriod.THREE_MONTHS,
    PerformancePeriod.SIX_MONTHS,
    PerformancePeriod.ONE_YEAR,
)

PERIOD_DOWNLOAD_MONTHS = {
    PerformancePeriod.ONE_MONTH: 3,
    PerformancePeriod.THREE_MONTHS: 5,
    PerformancePeriod.SIX_MONTHS: 8,
    PerformancePeriod.ONE_YEAR: 14,
}


@dataclass(
    frozen=True,
    slots=True,
)
class PerformanceFailure:
    """無法建立績效資料的 ETF 期間。"""

    etf_code: str
    etf_name: str
    period_code: PerformancePeriod
    category: str
    reason: str


@dataclass(
    frozen=True,
    slots=True,
)
class PerformancePeriodSummary:
    """單一績效期間的資料覆蓋摘要。"""

    period_code: PerformancePeriod
    candidate_count: int
    successful_count: int
    insufficient_history_count: int
    failed_count: int
    coverage_pct: float


@dataclass(
    frozen=True,
    slots=True,
)
class PerformancePipelineResult:
    """多期間績效批次結果。"""

    candidate_count: int
    requested_periods: tuple[
        PerformancePeriod,
        ...,
    ]
    download_month_count: int
    successful_count: int
    insufficient_history_count: int
    failed_count: int
    inserted_count: int
    updated_count: int
    period_summaries: tuple[
        PerformancePeriodSummary,
        ...,
    ]
    processed_path: Path
    rejected_path: Path
    report_path: Path


def write_json(
    file_path: Path,
    payload: object,
) -> None:
    """將資料寫入 UTF-8 JSON。"""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def normalize_periods(
    periods: (
        list[PerformancePeriod | str]
        | tuple[PerformancePeriod | str, ...]
        | None
    ),
) -> tuple[PerformancePeriod, ...]:
    """正規化並去除重複的績效期間。"""

    if periods is None:
        return DEFAULT_PERIODS

    if not periods:
        raise ValueError(
            "periods 至少必須包含一個期間"
        )

    normalized_set = {
        normalize_price_return_period(
            period
        )
        for period in periods
    }

    return tuple(
        period
        for period in DEFAULT_PERIODS
        if period in normalized_set
    )


def resolve_download_month_count(
    periods: tuple[
        PerformancePeriod,
        ...,
    ],
    month_count: int | None,
) -> int:
    """依最長期間決定下載月份數。"""

    required_month_count = max(
        PERIOD_DOWNLOAD_MONTHS[period]
        for period in periods
    )

    if month_count is None:
        return required_month_count

    if month_count < required_month_count:
        raise ValueError(
            "month_count 不足以計算指定期間；"
            f"至少需要 {required_month_count} 個月"
        )

    return month_count


def build_period_summaries(
    periods: tuple[
        PerformancePeriod,
        ...,
    ],
    candidate_count: int,
    counters: dict[
        PerformancePeriod,
        dict[str, int],
    ],
) -> tuple[
    PerformancePeriodSummary,
    ...,
]:
    """建立每個績效期間的覆蓋率摘要。"""

    summaries: list[
        PerformancePeriodSummary
    ] = []

    for period in periods:
        period_counter = counters[period]
        successful_count = (
            period_counter[
                "successful_count"
            ]
        )

        coverage_pct = (
            round(
                successful_count
                / candidate_count
                * 100,
                2,
            )
            if candidate_count
            else 0.0
        )

        summaries.append(
            PerformancePeriodSummary(
                period_code=period,
                candidate_count=(
                    candidate_count
                ),
                successful_count=(
                    successful_count
                ),
                insufficient_history_count=(
                    period_counter[
                        "insufficient_history_count"
                    ]
                ),
                failed_count=(
                    period_counter[
                        "failed_count"
                    ]
                ),
                coverage_pct=coverage_pct,
            )
        )

    return tuple(summaries)


def run_multi_period_performance_pipeline(
    database_path: str | Path | None = None,
    end_date: date | None = None,
    codes: list[str] | None = None,
    limit: int | None = None,
    periods: (
        list[PerformancePeriod | str]
        | tuple[PerformancePeriod | str, ...]
        | None
    ) = None,
    month_count: int | None = None,
    candidate_minimum_history_months: int = 0,
    include_bond: bool = False,
    request_interval_seconds: float = 0.4,
    inter_etf_interval_seconds: float = 0.5,
    processed_output_root: Path | None = None,
    rejected_output_root: Path | None = None,
    save_raw_snapshots: bool = True,
    verbose: bool = False,
) -> PerformancePipelineResult:
    """批次計算 ETF 多期間市價報酬率。

    每檔 ETF 只下載一次價格資料，再依序計算
    1M、3M、6M、1Y 中指定的期間。

    candidate_minimum_history_months 預設為 0，
    讓新上市 ETF 也可進入覆蓋率統計，並由
    各期間計算器判斷歷史是否充足。
    """

    if end_date is None:
        end_date = date.today()

    if candidate_minimum_history_months < 0:
        raise ValueError(
            "candidate_minimum_history_months "
            "不得小於 0"
        )

    normalized_periods = normalize_periods(
        periods
    )

    resolved_month_count = (
        resolve_download_month_count(
            periods=normalized_periods,
            month_count=month_count,
        )
    )

    candidates = list_performance_candidates(
        database_path=database_path,
        end_date=end_date,
        include_bond=include_bond,
        codes=codes,
        limit=limit,
        minimum_history_months=(
            candidate_minimum_history_months
        ),
    )

    if not candidates:
        raise ValueError(
            "沒有符合條件的 ETF 可計算績效"
        )

    performance_records: list[
        ETFPerformanceImportRecord
    ] = []

    daily_close_records = []

    failures: list[
        PerformanceFailure
    ] = []

    period_counters = {
        period: {
            "successful_count": 0,
            "insufficient_history_count": 0,
            "failed_count": 0,
        }
        for period in normalized_periods
    }

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        if verbose:
            print(
                f"[{index}/{len(candidates)}] "
                f"{candidate.code} "
                f"{candidate.name}"
            )

        try:
            price_records = (
                fetch_price_history(
                    etf_code=candidate.code,
                    end_date=end_date,
                    month_count=(
                        resolved_month_count
                    ),
                    request_interval_seconds=(
                        request_interval_seconds
                    ),
                )
            )

            if save_raw_snapshots:
                save_price_history_snapshot(
                    etf_code=candidate.code,
                    records=price_records,
                )

            daily_close_records.extend(price_records)

        except Exception as error:
            reason = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            for period in normalized_periods:
                period_counters[period][
                    "failed_count"
                ] += 1

                failures.append(
                    PerformanceFailure(
                        etf_code=candidate.code,
                        etf_name=candidate.name,
                        period_code=period,
                        category="error",
                        reason=reason,
                    )
                )

            if verbose:
                print(
                    f"  下載失敗：{reason}"
                )

        else:
            for period in normalized_periods:
                try:
                    calculation_result = (
                        calculate_price_return(
                            records=(
                                price_records
                            ),
                            period_code=period,
                        )
                    )

                    performance_record = (
                        ETFPerformanceImportRecord
                        .model_validate(
                            {
                                "etf_code": (
                                    calculation_result
                                    .etf_code
                                ),
                                "as_of_date": (
                                    calculation_result
                                    .as_of_date
                                ),
                                "period_code": (
                                    calculation_result
                                    .period_code
                                ),
                                "metric_code": (
                                    calculation_result
                                    .metric_code
                                ),
                                "return_pct": (
                                    calculation_result
                                    .return_pct
                                ),
                                "source_id": (
                                    calculation_result
                                    .source_id
                                ),
                                "import_batch_id": (
                                    None
                                ),
                                "source_updated_at": (
                                    None
                                ),
                            }
                        )
                    )

                    performance_records.append(
                        performance_record
                    )

                    period_counters[period][
                        "successful_count"
                    ] += 1

                    if verbose:
                        print(
                            f"  {period.value} "
                            "成功："
                            f"{performance_record.return_pct}%"
                        )

                except (
                    InsufficientPriceHistoryError
                ) as error:
                    period_counters[period][
                        "insufficient_history_count"
                    ] += 1

                    failures.append(
                        PerformanceFailure(
                            etf_code=(
                                candidate.code
                            ),
                            etf_name=(
                                candidate.name
                            ),
                            period_code=period,
                            category=(
                                "insufficient_history"
                            ),
                            reason=str(error),
                        )
                    )

                    if verbose:
                        print(
                            f"  {period.value} "
                            f"歷史不足：{error}"
                        )

                except Exception as error:
                    period_counters[period][
                        "failed_count"
                    ] += 1

                    reason = (
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

                    failures.append(
                        PerformanceFailure(
                            etf_code=(
                                candidate.code
                            ),
                            etf_name=(
                                candidate.name
                            ),
                            period_code=period,
                            category="error",
                            reason=reason,
                        )
                    )

                    if verbose:
                        print(
                            f"  {period.value} "
                            f"失敗：{reason}"
                        )

        if (
            inter_etf_interval_seconds > 0
            and index < len(candidates)
        ):
            time.sleep(
                inter_etf_interval_seconds
            )

    upsert_daily_close_records(
        records=daily_close_records,
        database_path=database_path,
    )

    if performance_records:
        upsert_summary = (
            upsert_performance_records(
                records=performance_records,
                database_path=database_path,
            )
        )

    else:
        upsert_summary = (
            PerformanceUpsertSummary(
                total_records=0,
                inserted_records=0,
                updated_records=0,
            )
        )

    generated_at = datetime.now(
        timezone.utc
    )

    timestamp = generated_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    if processed_output_root is None:
        processed_output_root = (
            PROCESSED_DATA_DIR
            / "performance"
            / SOURCE_ID
        )

    if rejected_output_root is None:
        rejected_output_root = (
            REJECTED_DATA_DIR
            / "performance"
            / SOURCE_ID
        )

    processed_payload = [
        record.model_dump(
            mode="json"
        )
        for record in performance_records
    ]

    rejected_payload = [
        {
            "etf_code": failure.etf_code,
            "etf_name": failure.etf_name,
            "period_code": (
                failure.period_code.value
            ),
            "category": failure.category,
            "reason": failure.reason,
        }
        for failure in failures
    ]

    output_prefix = (
        "six_month_performance"
        if normalized_periods
        == (
            PerformancePeriod.SIX_MONTHS,
        )
        else "multi_period_performance"
    )

    processed_path = (
        processed_output_root
        / f"{output_prefix}_{timestamp}.json"
    )

    rejected_path = (
        rejected_output_root
        / f"{output_prefix}_{timestamp}.json"
    )

    report_path = (
        processed_output_root
        / (
            f"{output_prefix}_{timestamp}"
            ".report.json"
        )
    )

    write_json(
        processed_path,
        processed_payload,
    )

    write_json(
        processed_output_root / "latest.json",
        processed_payload,
    )

    write_json(
        rejected_path,
        rejected_payload,
    )

    write_json(
        rejected_output_root / "latest.json",
        rejected_payload,
    )

    period_summaries = (
        build_period_summaries(
            periods=normalized_periods,
            candidate_count=len(candidates),
            counters=period_counters,
        )
    )

    insufficient_history_count = sum(
        summary.insufficient_history_count
        for summary in period_summaries
    )

    failed_count = sum(
        summary.failed_count
        for summary in period_summaries
    )

    report: dict[str, Any] = {
        "schema_version": 2,
        "source_id": SOURCE_ID,
        "period_code": (
            normalized_periods[0].value
            if len(normalized_periods) == 1
            else None
        ),
        "period_codes": [
            period.value
            for period in normalized_periods
        ],
        "metric_code": (
            PerformanceMetric.PRICE_RETURN.value
        ),
        "metric_name": (
            "market_price_return"
        ),
        "generated_at": (
            generated_at.isoformat()
        ),
        "requested_end_date": (
            end_date.isoformat()
        ),
        "download_month_count": (
            resolved_month_count
        ),
        "candidate_minimum_history_months": (
            candidate_minimum_history_months
        ),
        "candidate_count": len(candidates),
        "successful_count": len(
            performance_records
        ),
        "insufficient_history_count": (
            insufficient_history_count
        ),
        "failed_count": failed_count,
        "inserted_count": (
            upsert_summary.inserted_records
        ),
        "updated_count": (
            upsert_summary.updated_records
        ),
        "period_summaries": [
            {
                "period_code": (
                    summary.period_code.value
                ),
                "candidate_count": (
                    summary.candidate_count
                ),
                "successful_count": (
                    summary.successful_count
                ),
                "insufficient_history_count": (
                    summary
                    .insufficient_history_count
                ),
                "failed_count": (
                    summary.failed_count
                ),
                "coverage_pct": (
                    summary.coverage_pct
                ),
            }
            for summary in period_summaries
        ],
        "processed_path": str(
            processed_path
        ),
        "rejected_path": str(
            rejected_path
        ),
        "includes_distributions": False,
        "notes": (
            "多期間市價報酬率，"
            "各期間分開計算及排名，"
            "不包含配息再投資。"
        ),
    }

    write_json(
        report_path,
        report,
    )

    write_json(
        processed_output_root
        / "latest.report.json",
        report,
    )

    return PerformancePipelineResult(
        candidate_count=len(candidates),
        requested_periods=(
            normalized_periods
        ),
        download_month_count=(
            resolved_month_count
        ),
        successful_count=len(
            performance_records
        ),
        insufficient_history_count=(
            insufficient_history_count
        ),
        failed_count=failed_count,
        inserted_count=(
            upsert_summary.inserted_records
        ),
        updated_count=(
            upsert_summary.updated_records
        ),
        period_summaries=period_summaries,
        processed_path=processed_path,
        rejected_path=rejected_path,
        report_path=report_path,
    )


def run_six_month_performance_pipeline(
    database_path: str | Path | None = None,
    end_date: date | None = None,
    codes: list[str] | None = None,
    limit: int | None = None,
    month_count: int = 8,
    include_bond: bool = False,
    request_interval_seconds: float = 0.4,
    inter_etf_interval_seconds: float = 0.5,
    processed_output_root: Path | None = None,
    rejected_output_root: Path | None = None,
    save_raw_snapshots: bool = True,
    verbose: bool = False,
) -> PerformancePipelineResult:
    """保留原六個月 Pipeline 的相容介面。"""

    return run_multi_period_performance_pipeline(
        database_path=database_path,
        end_date=end_date,
        codes=codes,
        limit=limit,
        periods=(
            PerformancePeriod.SIX_MONTHS,
        ),
        month_count=month_count,
        include_bond=include_bond,
        candidate_minimum_history_months=6,
        request_interval_seconds=(
            request_interval_seconds
        ),
        inter_etf_interval_seconds=(
            inter_etf_interval_seconds
        ),
        processed_output_root=(
            processed_output_root
        ),
        rejected_output_root=(
            rejected_output_root
        ),
        save_raw_snapshots=(
            save_raw_snapshots
        ),
        verbose=verbose,
    )


def parse_date_argument(
    value: str,
) -> date:
    """解析 YYYY-MM-DD 日期參數。"""

    try:
        return date.fromisoformat(
            value
        )

    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "日期格式必須是 YYYY-MM-DD"
        ) from error


def build_argument_parser(
) -> argparse.ArgumentParser:
    """建立命令列參數。"""

    parser = argparse.ArgumentParser(
        description=(
            "批次計算 ETF 多期間市價報酬率"
        )
    )

    parser.add_argument(
        "--codes",
        nargs="*",
        help=(
            "只處理指定 ETF，"
            "例如 --codes 0050 00918"
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="最多處理 ETF 數量",
    )

    parser.add_argument(
        "--end-date",
        type=parse_date_argument,
        default=None,
        help="截止日期 YYYY-MM-DD",
    )

    parser.add_argument(
        "--periods",
        nargs="+",
        choices=tuple(
            period.value
            for period in DEFAULT_PERIODS
        ),
        default=[
            period.value
            for period in DEFAULT_PERIODS
        ],
        help=(
            "計算期間，預設 1M 3M 6M 1Y"
        ),
    )

    parser.add_argument(
        "--months",
        type=int,
        default=None,
        help=(
            "下載月份數；未指定時依最長期間"
            "自動使用 3、5、8 或 14 個月"
        ),
    )

    parser.add_argument(
        "--include-bond",
        action="store_true",
        help=(
            "包含債券 ETF；詳細資料頁全市場快照使用"
        ),
    )

    parser.add_argument(
        "--request-interval",
        type=float,
        default=0.4,
        help="同一 ETF 每月請求間隔秒數",
    )

    parser.add_argument(
        "--between-etf",
        type=float,
        default=0.5,
        help="每檔 ETF 之間等待秒數",
    )

    parser.add_argument(
        "--no-raw-snapshot",
        action="store_true",
        help="不保存個別 ETF 價格快照",
    )

    return parser


def main() -> None:
    """執行多期間績效批次 Pipeline。"""

    arguments = (
        build_argument_parser()
        .parse_args()
    )

    print("開始執行 ETF 多期間績效 Pipeline")
    print(
        "績效期間："
        + ", ".join(arguments.periods)
    )
    print("績效定義：市價報酬率")
    print("包含配息再投資：否")
    print("-" * 70)

    result = (
        run_multi_period_performance_pipeline(
            end_date=arguments.end_date,
            codes=arguments.codes,
            limit=arguments.limit,
            periods=arguments.periods,
            month_count=arguments.months,
            include_bond=arguments.include_bond,
            request_interval_seconds=(
                arguments.request_interval
            ),
            inter_etf_interval_seconds=(
                arguments.between_etf
            ),
            save_raw_snapshots=(
                not arguments.no_raw_snapshot
            ),
            verbose=True,
        )
    )

    print("-" * 70)
    print("ETF 多期間績效 Pipeline 完成")
    print(
        f"候選 ETF：{result.candidate_count}"
    )
    print(
        "下載月份："
        f"{result.download_month_count}"
    )
    print(
        "成功績效紀錄："
        f"{result.successful_count}"
    )
    print(
        "歷史不足期間："
        f"{result.insufficient_history_count}"
    )
    print(
        "執行失敗期間："
        f"{result.failed_count}"
    )

    for summary in result.period_summaries:
        print(
            f"{summary.period_code.value}: "
            f"成功 {summary.successful_count}，"
            "歷史不足 "
            f"{summary.insufficient_history_count}，"
            f"失敗 {summary.failed_count}，"
            f"覆蓋率 {summary.coverage_pct:.2f}%"
        )

    print(
        f"新增資料：{result.inserted_count}"
    )
    print(
        f"更新資料：{result.updated_count}"
    )
    print(
        f"處理結果：{result.processed_path}"
    )
    print(
        f"拒絕資料：{result.rejected_path}"
    )
    print(
        f"品質報告：{result.report_path}"
    )


if __name__ == "__main__":
    main()
