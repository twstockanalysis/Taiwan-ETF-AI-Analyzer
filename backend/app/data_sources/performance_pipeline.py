"""ETF 六個月市價報酬率批次 Pipeline。"""

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
)
from backend.app.repositories.performance_repository import (
    PerformanceUpsertSummary,
    list_performance_candidates,
    upsert_performance_records,
)
from backend.app.services.performance_calculator import (
    InsufficientPriceHistoryError,
    calculate_six_month_price_return,
)


SOURCE_ID = "twse_stock_day"
PERIOD_CODE = "6M"


@dataclass(
    frozen=True,
    slots=True,
)
class PerformanceFailure:
    """無法建立績效資料的 ETF。"""

    etf_code: str
    etf_name: str
    category: str
    reason: str


@dataclass(
    frozen=True,
    slots=True,
)
class PerformancePipelineResult:
    """六個月績效批次結果。"""

    candidate_count: int
    successful_count: int
    insufficient_history_count: int
    failed_count: int
    inserted_count: int
    updated_count: int
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


def run_six_month_performance_pipeline(
    database_path: str | Path | None = None,
    end_date: date | None = None,
    codes: list[str] | None = None,
    limit: int | None = None,
    month_count: int = 8,
    request_interval_seconds: float = 0.4,
    inter_etf_interval_seconds: float = 0.5,
    processed_output_root: Path | None = None,
    rejected_output_root: Path | None = None,
    save_raw_snapshots: bool = True,
    verbose: bool = False,
) -> PerformancePipelineResult:
    """批次計算非債券 ETF 六個月市價報酬率。

    Args:
        database_path:
            SQLite 資料庫路徑。
        end_date:
            下載截止日期。
        codes:
            只處理指定 ETF。
        limit:
            最多處理 ETF 數量。
        month_count:
            每檔下載的月份數。
        request_interval_seconds:
            同一 ETF 每月請求間隔。
        inter_etf_interval_seconds:
            ETF 與 ETF 之間的等待時間。
        processed_output_root:
            正規化資料輸出目錄。
        rejected_output_root:
            失敗資料輸出目錄。
        save_raw_snapshots:
            是否保存每檔價格快照。
        verbose:
            是否顯示逐檔進度。

    Returns:
        PerformancePipelineResult:
            績效批次處理結果。
    """

    if end_date is None:
        end_date = date.today()

    if month_count < 7:
        raise ValueError(
            "month_count 至少必須為 7"
        )

    candidates = list_performance_candidates(
        database_path=database_path,
        end_date=end_date,
        include_bond=False,
        codes=codes,
        limit=limit,
    )

    if not candidates:
        raise ValueError(
            "沒有符合條件的 ETF 可計算績效"
        )

    performance_records: list[
        ETFPerformanceImportRecord
    ] = []

    failures: list[
        PerformanceFailure
    ] = []

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
                    month_count=month_count,
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

            calculation_result = (
                calculate_six_month_price_return(
                    price_records
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
                        "return_pct": (
                            calculation_result
                            .return_pct
                        ),
                        "source_id": (
                            calculation_result
                            .source_id
                        ),
                        "import_batch_id": None,
                        "source_updated_at": None,
                    }
                )
            )

            performance_records.append(
                performance_record
            )

            if verbose:
                print(
                    "  成功："
                    f"{performance_record.return_pct}%"
                )

        except InsufficientPriceHistoryError as error:
            failures.append(
                PerformanceFailure(
                    etf_code=candidate.code,
                    etf_name=candidate.name,
                    category=(
                        "insufficient_history"
                    ),
                    reason=str(error),
                )
            )

            if verbose:
                print(
                    f"  跳過：{error}"
                )

        except Exception as error:
            failures.append(
                PerformanceFailure(
                    etf_code=candidate.code,
                    etf_name=candidate.name,
                    category="error",
                    reason=(
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                )
            )

            if verbose:
                print(
                    "  失敗："
                    f"{type(error).__name__}: "
                    f"{error}"
                )

        if (
            inter_etf_interval_seconds > 0
            and index < len(candidates)
        ):
            time.sleep(
                inter_etf_interval_seconds
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
            "category": failure.category,
            "reason": failure.reason,
        }
        for failure in failures
    ]

    processed_path = (
        processed_output_root
        / (
            f"six_month_performance_"
            f"{timestamp}.json"
        )
    )

    rejected_path = (
        rejected_output_root
        / (
            f"six_month_performance_"
            f"{timestamp}.json"
        )
    )

    report_path = (
        processed_output_root
        / (
            f"six_month_performance_"
            f"{timestamp}.report.json"
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

    insufficient_history_count = sum(
        failure.category
        == "insufficient_history"
        for failure in failures
    )

    failed_count = sum(
        failure.category == "error"
        for failure in failures
    )

    report: dict[str, Any] = {
        "schema_version": 1,
        "source_id": SOURCE_ID,
        "period_code": PERIOD_CODE,
        "metric_name": (
            "six_month_market_price_return"
        ),
        "generated_at": (
            generated_at.isoformat()
        ),
        "requested_end_date": (
            end_date.isoformat()
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
        "processed_path": str(
            processed_path
        ),
        "rejected_path": str(
            rejected_path
        ),
        "includes_distributions": False,
        "notes": (
            "六個月市價報酬率，"
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
        processed_path=processed_path,
        rejected_path=rejected_path,
        report_path=report_path,
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
            "批次計算 ETF 六個月市價報酬率"
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
        "--months",
        type=int,
        default=8,
        help="每檔下載月份數，預設 8",
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
    """執行六個月績效批次 Pipeline。"""

    arguments = (
        build_argument_parser()
        .parse_args()
    )

    print("開始執行 ETF 六個月績效 Pipeline")
    print(
        "績效定義：六個月市價報酬率"
    )
    print(
        "包含配息再投資：否"
    )
    print("-" * 70)

    result = (
        run_six_month_performance_pipeline(
            end_date=arguments.end_date,
            codes=arguments.codes,
            limit=arguments.limit,
            month_count=arguments.months,
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
    print("ETF 六個月績效 Pipeline 完成")
    print(
        f"候選 ETF："
        f"{result.candidate_count}"
    )
    print(
        f"成功計算："
        f"{result.successful_count}"
    )
    print(
        "歷史不足："
        f"{result.insufficient_history_count}"
    )
    print(
        f"執行失敗："
        f"{result.failed_count}"
    )
    print(
        f"新增資料："
        f"{result.inserted_count}"
    )
    print(
        f"更新資料："
        f"{result.updated_count}"
    )
    print(
        f"處理結果："
        f"{result.processed_path}"
    )
    print(
        f"拒絕資料："
        f"{result.rejected_path}"
    )
    print(
        f"品質報告："
        f"{result.report_path}"
    )


if __name__ == "__main__":
    main()