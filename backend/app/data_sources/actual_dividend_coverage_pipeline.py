"""正式配息覆蓋率與待處理佇列 Pipeline。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.actual_dividend_coverage_report import (
    build_actual_dividend_coverage_report,
    save_actual_dividend_coverage_artifacts,
)
from backend.app.repositories.dividend_quality_repository import (
    DividendReviewQueueSyncSummary,
    build_actual_dividend_coverage_summary,
    count_dividend_review_queue,
    list_dividend_coverage_events,
    list_dividend_review_queue,
    synchronize_dividend_review_queue,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendCoveragePipelineResult:
    """正式配息覆蓋率 Pipeline 結果。"""

    coverage_summary: dict
    queue_sync_summary: (
        DividendReviewQueueSyncSummary
    )
    review_queue_count: int
    queue_snapshot_path: Path
    quality_report_path: Path


def run_actual_dividend_coverage_pipeline(
    database_path: str | Path | None = None,
    output_root: Path | None = None,
    run_at: datetime | None = None,
) -> ActualDividendCoveragePipelineResult:
    """同步佇列並輸出正式配息品質報告。"""

    target_database_path = (
        initialize_database(
            database_path
        )
    )

    if run_at is None:
        run_at = datetime.now(
            timezone.utc
        )

    if run_at.tzinfo is None:
        raise ValueError(
            "run_at 必須包含時區"
        )

    sync_summary = (
        synchronize_dividend_review_queue(
            database_path=(
                target_database_path
            ),
            run_at=run_at,
        )
    )

    coverage_summary = (
        build_actual_dividend_coverage_summary(
            database_path=(
                target_database_path
            )
        )
    )

    events = list_dividend_coverage_events(
        database_path=(
            target_database_path
        )
    )

    review_queue_count = (
        count_dividend_review_queue(
            database_path=(
                target_database_path
            )
        )
    )

    queue_items = (
        list_dividend_review_queue(
            database_path=(
                target_database_path
            ),
            limit=max(
                review_queue_count,
                1,
            ),
        )
        if review_queue_count
        else []
    )

    report = (
        build_actual_dividend_coverage_report(
            summary=coverage_summary,
            sync_summary=sync_summary,
            events=events,
            queue_items=queue_items,
            created_at=run_at,
        )
    )

    artifacts = (
        save_actual_dividend_coverage_artifacts(
            report=report,
            queue_items=queue_items,
            output_root=output_root,
            created_at=run_at,
        )
    )

    return (
        ActualDividendCoveragePipelineResult(
            coverage_summary=(
                coverage_summary
            ),
            queue_sync_summary=(
                sync_summary
            ),
            review_queue_count=(
                review_queue_count
            ),
            queue_snapshot_path=(
                artifacts.queue_snapshot_path
            ),
            quality_report_path=(
                artifacts.quality_report_path
            ),
        )
    )


def build_argument_parser(
) -> argparse.ArgumentParser:
    """建立命令列參數。"""

    return argparse.ArgumentParser(
        description=(
            "同步正式配息覆蓋率與"
            "人工來源審核佇列"
        )
    )


def main(
    argv: list[str] | None = None,
) -> None:
    """執行正式配息覆蓋率 Pipeline。"""

    build_argument_parser().parse_args(
        argv
    )

    print(
        "開始執行正式配息覆蓋率 Pipeline"
    )

    result = (
        run_actual_dividend_coverage_pipeline()
    )

    coverage = (
        result.coverage_summary
    )

    print("-" * 70)
    print("正式配息覆蓋率 Pipeline 執行成功")
    print(
        "配息事件："
        f"{coverage['total_dividend_count']}"
    )
    print(
        "ACTUAL 覆蓋事件："
        f"{coverage['actual_component_event_count']}"
    )
    print(
        "ACTUAL 76W 事件："
        f"{coverage['actual_76w_event_count']}"
    )
    print(
        "來源文件覆蓋事件："
        f"{coverage['source_document_event_count']}"
    )
    print(
        "待處理佇列："
        f"{result.review_queue_count}"
    )
    print(
        "新建項目："
        f"{result.queue_sync_summary.created_item_count}"
    )
    print(
        "自動解決項目："
        f"{result.queue_sync_summary.resolved_item_count}"
    )
    print(
        "佇列快照："
        f"{result.queue_snapshot_path}"
    )
    print(
        "品質報告："
        f"{result.quality_report_path}"
    )


if __name__ == "__main__":
    main()
