"""正式配息覆蓋率報告與佇列快照。"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.config.settings import (
    PROCESSED_DATA_DIR,
)
from backend.app.repositories.dividend_quality_repository import (
    DividendReviewQueueSyncSummary,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ActualDividendCoverageArtifactPaths:
    """正式配息覆蓋率產物位置。"""

    queue_snapshot_path: Path
    quality_report_path: Path


def write_json(
    file_path: Path,
    payload: object,
) -> None:
    """寫入 UTF-8 JSON。"""

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


def build_breakdown(
    events: list[dict[str, Any]],
    key_name: str,
) -> list[dict[str, Any]]:
    """依指定欄位彙整事件覆蓋狀態。"""

    groups: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for event in events:
        key = str(
            event.get(key_name)
            or "UNKNOWN"
        )

        groups.setdefault(
            key,
            [],
        ).append(
            event
        )

    result: list[
        dict[str, Any]
    ] = []

    for key, group in sorted(
        groups.items()
    ):
        result.append(
            {
                key_name: key,
                "total_dividend_count": len(
                    group
                ),
                "actual_component_event_count": sum(
                    item[
                        "has_actual_components"
                    ]
                    for item in group
                ),
                "actual_76w_event_count": sum(
                    item["has_actual_76w"]
                    for item in group
                ),
                "source_document_event_count": sum(
                    item[
                        "has_source_document"
                    ]
                    for item in group
                ),
            }
        )

    return result


def build_year_breakdown(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """依配息事件主要日期年份彙整。"""

    enriched: list[
        dict[str, Any]
    ] = []

    for event in events:
        event_date = (
            event["ex_dividend_date"]
            or event["record_date"]
            or event["payment_date"]
            or event["announcement_date"]
        )

        enriched.append(
            {
                **event,
                "event_year": (
                    str(event_date)[:4]
                    if event_date
                    else "UNKNOWN"
                ),
            }
        )

    return build_breakdown(
        enriched,
        "event_year",
    )


def build_actual_dividend_coverage_report(
    *,
    summary: dict[str, Any],
    sync_summary: (
        DividendReviewQueueSyncSummary
    ),
    events: list[dict[str, Any]],
    queue_items: list[dict[str, Any]],
    created_at: datetime,
) -> dict[str, Any]:
    """建立全站正式配息覆蓋率品質報告。"""

    issue_counts = Counter(
        item["issue_type"]
        for item in queue_items
    )

    status_counts = Counter(
        item["status"]
        for item in queue_items
    )

    warnings: list[str] = []

    if summary[
        "total_dividend_count"
    ] == 0:
        warnings.append(
            "目前沒有任何配息事件"
        )

    if summary[
        "missing_actual_component_event_count"
    ]:
        warnings.append(
            "部分配息事件尚缺正式 ACTUAL 組成"
        )

    if summary[
        "missing_source_document_event_count"
    ]:
        warnings.append(
            "部分配息事件尚缺可追溯正式來源文件"
        )

    return {
        "schema_version": 1,
        "generated_at": (
            created_at.isoformat()
        ),
        "status": "success",
        "coverage": summary,
        "queue_sync": asdict(
            sync_summary
        ),
        "queue_status_counts": [
            {
                "status": key,
                "count": value,
            }
            for key, value
            in status_counts.most_common()
        ],
        "queue_issue_counts": [
            {
                "issue_type": key,
                "count": value,
            }
            for key, value
            in issue_counts.most_common()
        ],
        "by_etf": build_breakdown(
            events,
            "etf_code",
        ),
        "by_year": build_year_breakdown(
            events
        ),
        "by_dividend_source": (
            build_breakdown(
                events,
                "dividend_source_id",
            )
        ),
        "warnings": warnings,
        "notes": (
            "actual_76w_event_count 只計算"
            " component_basis=ACTUAL 且"
            " component_code=76W 的事件。"
            "正式揭露 0% 仍視為已有 76W 紀錄；"
            "EST_REALIZED_CAPITAL_GAIN 不計入。"
        ),
    }


def save_actual_dividend_coverage_artifacts(
    *,
    report: dict[str, Any],
    queue_items: list[dict[str, Any]],
    output_root: Path | None = None,
    created_at: datetime | None = None,
) -> ActualDividendCoverageArtifactPaths:
    """保存待處理佇列快照與品質報告。"""

    if created_at is None:
        created_at = datetime.now(
            timezone.utc
        )

    timestamp = created_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    if output_root is None:
        queue_directory = (
            PROCESSED_DATA_DIR
            / "dividends"
            / "review_queue"
        )

        report_directory = (
            PROCESSED_DATA_DIR
            / "reports"
            / "dividends"
            / "coverage"
        )

    else:
        queue_directory = (
            output_root / "review_queue"
        )

        report_directory = (
            output_root / "quality"
        )

    queue_path = (
        queue_directory
        / (
            f"review_queue_"
            f"{timestamp}.json"
        )
    )

    report_path = (
        report_directory
        / (
            f"coverage_"
            f"{timestamp}.report.json"
        )
    )

    queue_payload = {
        "schema_version": 1,
        "generated_at": (
            created_at.isoformat()
        ),
        "items": queue_items,
    }

    write_json(
        queue_path,
        queue_payload,
    )

    write_json(
        queue_directory / "latest.json",
        queue_payload,
    )

    write_json(
        report_path,
        report,
    )

    write_json(
        report_directory / "latest.json",
        report,
    )

    return ActualDividendCoverageArtifactPaths(
        queue_snapshot_path=queue_path,
        quality_report_path=report_path,
    )
