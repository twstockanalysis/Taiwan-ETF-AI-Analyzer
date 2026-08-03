"""正式配息覆蓋率與人工審核佇列 Repository。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sqlite3

from backend.app.database.connection import (
    get_connection,
)
from backend.app.models.dividend_quality import (
    DividendReviewIssueType,
    DividendReviewStatus,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DividendReviewQueueSyncSummary:
    """待處理佇列同步結果。"""

    evaluated_event_count: int
    created_item_count: int
    reopened_item_count: int
    resolved_item_count: int
    unchanged_item_count: int


def normalize_optional_etf_code(
    etf_code: str | None,
) -> str | None:
    """正規化可選 ETF 代號。"""

    if etf_code is None:
        return None

    normalized = etf_code.strip().upper()

    if not normalized:
        return None

    return normalized


def normalize_enum_value(
    value,
    enum_type,
    field_name: str,
) -> str | None:
    """正規化可選 StrEnum 或文字值。"""

    if value is None:
        return None

    if isinstance(
        value,
        enum_type,
    ):
        return value.value

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} 必須是文字"
        )

    normalized = value.strip().upper()

    try:
        return enum_type(
            normalized
        ).value

    except ValueError as error:
        raise ValueError(
            f"{field_name} 不支援："
            f"{normalized}"
        ) from error


def _fetch_dividend_coverage_events(
    connection: sqlite3.Connection,
    etf_code: str | None = None,
) -> list[dict[str, Any]]:
    """使用既有連線取得每筆配息事件覆蓋狀態。"""

    normalized_code = (
        normalize_optional_etf_code(
            etf_code
        )
    )

    where_clause = ""
    parameters: list[Any] = []

    if normalized_code is not None:
        where_clause = (
            "WHERE d.etf_code = ?"
        )
        parameters.append(
            normalized_code
        )

    rows = connection.execute(
        f"""
        SELECT
            d.id AS dividend_id,
            d.etf_code,
            d.source_event_id,
            d.announcement_date,
            d.ex_dividend_date,
            d.record_date,
            d.payment_date,
            d.amount_per_unit,
            d.currency,
            d.source_id AS dividend_source_id,

            EXISTS (
                SELECT 1
                FROM etf_dividend_component AS c
                WHERE c.dividend_id = d.id
                  AND c.component_basis = 'ESTIMATED'
            ) AS has_estimated_components,

            EXISTS (
                SELECT 1
                FROM etf_dividend_component AS c
                WHERE c.dividend_id = d.id
                  AND c.component_basis = 'ACTUAL'
            ) AS has_actual_components,

            EXISTS (
                SELECT 1
                FROM etf_dividend_component AS c
                WHERE c.dividend_id = d.id
                  AND c.component_basis = 'ACTUAL'
                  AND c.component_code = '76W'
            ) AS has_actual_76w,

            EXISTS (
                SELECT 1
                FROM etf_dividend_component AS c
                INNER JOIN dividend_source_document AS sd
                    ON sd.import_batch_id = c.import_batch_id
                WHERE c.dividend_id = d.id
                  AND c.component_basis = 'ACTUAL'
                  AND sd.parse_status = 'parsed'
                  AND sd.information_basis = 'ACTUAL'
            ) AS has_source_document,

            (
                SELECT GROUP_CONCAT(
                    DISTINCT c.source_id
                )
                FROM etf_dividend_component AS c
                WHERE c.dividend_id = d.id
                  AND c.component_basis = 'ACTUAL'
            ) AS actual_source_ids,

            (
                SELECT MAX(sd.id)
                FROM etf_dividend_component AS c
                INNER JOIN dividend_source_document AS sd
                    ON sd.import_batch_id = c.import_batch_id
                WHERE c.dividend_id = d.id
                  AND c.component_basis = 'ACTUAL'
                  AND sd.parse_status = 'parsed'
                  AND sd.information_basis = 'ACTUAL'
            ) AS latest_source_document_id

        FROM etf_dividend AS d
        {where_clause}
        ORDER BY
            COALESCE(
                d.ex_dividend_date,
                d.record_date,
                d.payment_date,
                d.announcement_date
            ) DESC,
            d.id DESC;
        """,
        parameters,
    ).fetchall()

    result: list[
        dict[str, Any]
    ] = []

    for row in rows:
        item = dict(row)

        for field_name in (
            "has_estimated_components",
            "has_actual_components",
            "has_actual_76w",
            "has_source_document",
        ):
            item[field_name] = bool(
                item[field_name]
            )

        result.append(
            item
        )

    return result


def list_dividend_coverage_events(
    database_path: str | Path | None = None,
    etf_code: str | None = None,
) -> list[dict[str, Any]]:
    """列出每筆配息事件的正式資料覆蓋狀態。"""

    connection = get_connection(
        database_path
    )

    try:
        return _fetch_dividend_coverage_events(
            connection,
            etf_code=etf_code,
        )

    finally:
        connection.close()


def calculate_coverage_pct(
    covered_count: int,
    total_count: int,
) -> float | None:
    """計算覆蓋率；沒有事件時保留缺資料語意。"""

    if total_count == 0:
        return None

    return round(
        covered_count
        / total_count
        * 100,
        6,
    )


def build_actual_dividend_coverage_summary(
    database_path: str | Path | None = None,
    etf_code: str | None = None,
) -> dict[str, Any]:
    """建立正式配息、76W 與來源文件覆蓋摘要。"""

    normalized_code = (
        normalize_optional_etf_code(
            etf_code
        )
    )

    events = list_dividend_coverage_events(
        database_path=database_path,
        etf_code=normalized_code,
    )

    total_count = len(events)

    estimated_count = sum(
        item[
            "has_estimated_components"
        ]
        for item in events
    )

    actual_count = sum(
        item[
            "has_actual_components"
        ]
        for item in events
    )

    actual_76w_count = sum(
        item["has_actual_76w"]
        for item in events
    )

    source_document_count = sum(
        item["has_source_document"]
        for item in events
    )

    return {
        "etf_code": normalized_code,
        "total_dividend_count": (
            total_count
        ),
        "estimated_component_event_count": (
            estimated_count
        ),
        "actual_component_event_count": (
            actual_count
        ),
        "actual_76w_event_count": (
            actual_76w_count
        ),
        "source_document_event_count": (
            source_document_count
        ),
        "missing_actual_component_event_count": (
            total_count - actual_count
        ),
        "missing_source_document_event_count": (
            total_count
            - source_document_count
        ),
        "actual_component_coverage_pct": (
            calculate_coverage_pct(
                actual_count,
                total_count,
            )
        ),
        "actual_76w_coverage_pct": (
            calculate_coverage_pct(
                actual_76w_count,
                total_count,
            )
        ),
        "source_document_coverage_pct": (
            calculate_coverage_pct(
                source_document_count,
                total_count,
            )
        ),
    }


def build_review_queue_filter_clause(
    *,
    status: (
        DividendReviewStatus
        | str
        | None
    ) = None,
    etf_code: str | None = None,
    issue_type: (
        DividendReviewIssueType
        | str
        | None
    ) = None,
) -> tuple[str, list[Any]]:
    """建立審核佇列共用篩選條件。"""

    conditions: list[str] = []
    parameters: list[Any] = []

    normalized_status = (
        normalize_enum_value(
            status,
            DividendReviewStatus,
            "status",
        )
    )

    normalized_issue_type = (
        normalize_enum_value(
            issue_type,
            DividendReviewIssueType,
            "issue_type",
        )
    )

    normalized_code = (
        normalize_optional_etf_code(
            etf_code
        )
    )

    if normalized_status is not None:
        conditions.append(
            "q.status = ?"
        )
        parameters.append(
            normalized_status
        )

    if normalized_code is not None:
        conditions.append(
            "d.etf_code = ?"
        )
        parameters.append(
            normalized_code
        )

    if normalized_issue_type is not None:
        conditions.append(
            "q.issue_type = ?"
        )
        parameters.append(
            normalized_issue_type
        )

    if not conditions:
        return "", parameters

    return (
        "WHERE "
        + " AND ".join(conditions),
        parameters,
    )


def count_dividend_review_queue(
    database_path: str | Path | None = None,
    *,
    status: (
        DividendReviewStatus
        | str
        | None
    ) = None,
    etf_code: str | None = None,
    issue_type: (
        DividendReviewIssueType
        | str
        | None
    ) = None,
) -> int:
    """計算符合條件的待處理項目。"""

    (
        where_clause,
        parameters,
    ) = build_review_queue_filter_clause(
        status=status,
        etf_code=etf_code,
        issue_type=issue_type,
    )

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM dividend_source_review_queue AS q
            INNER JOIN etf_dividend AS d
                ON d.id = q.dividend_id
            {where_clause};
            """,
            parameters,
        ).fetchone()

        return int(
            row["total"]
        )

    finally:
        connection.close()


def list_dividend_review_queue(
    database_path: str | Path | None = None,
    *,
    status: (
        DividendReviewStatus
        | str
        | None
    ) = None,
    etf_code: str | None = None,
    issue_type: (
        DividendReviewIssueType
        | str
        | None
    ) = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """分頁列出正式配息來源審核佇列。"""

    if limit < 1:
        raise ValueError(
            "limit 必須大於 0"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    (
        where_clause,
        parameters,
    ) = build_review_queue_filter_clause(
        status=status,
        etf_code=etf_code,
        issue_type=issue_type,
    )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            SELECT
                q.id AS queue_id,
                q.dividend_id,
                d.etf_code,
                d.source_event_id,
                d.ex_dividend_date,
                d.amount_per_unit,
                d.currency,
                q.issue_type,
                q.suggested_source_id,
                q.priority,
                q.status,
                q.notes,
                q.resolution_document_id,
                q.last_evaluated_at,
                q.resolved_at,
                q.created_at,
                q.updated_at
            FROM dividend_source_review_queue AS q
            INNER JOIN etf_dividend AS d
                ON d.id = q.dividend_id
            {where_clause}
            ORDER BY
                CASE q.status
                    WHEN 'PENDING' THEN 0
                    WHEN 'IN_REVIEW' THEN 1
                    WHEN 'SKIPPED' THEN 2
                    ELSE 3
                END,
                q.priority,
                COALESCE(
                    d.ex_dividend_date,
                    d.record_date,
                    d.payment_date,
                    d.announcement_date
                ) DESC,
                q.id
            LIMIT ?
            OFFSET ?;
            """,
            [
                *parameters,
                limit,
                offset,
            ],
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_dividend_review_queue_item(
    queue_id: int,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """取得單一正式配息審核項目。"""

    if queue_id < 1:
        raise ValueError(
            "queue_id 必須大於 0"
        )

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            """
            SELECT
                q.id AS queue_id,
                q.dividend_id,
                d.etf_code,
                d.source_event_id,
                d.ex_dividend_date,
                d.amount_per_unit,
                d.currency,
                q.issue_type,
                q.suggested_source_id,
                q.priority,
                q.status,
                q.notes,
                q.resolution_document_id,
                q.last_evaluated_at,
                q.resolved_at,
                q.created_at,
                q.updated_at
            FROM dividend_source_review_queue AS q
            INNER JOIN etf_dividend AS d
                ON d.id = q.dividend_id
            WHERE q.id = ?;
            """,
            (queue_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def set_dividend_review_queue_status(
    *,
    queue_id: int,
    status: (
        DividendReviewStatus
        | str
    ),
    database_path: str | Path | None = None,
    notes: str | None = None,
    resolution_document_id: int | None = None,
    changed_at: datetime | None = None,
) -> None:
    """供管理流程更新審核狀態與備註。"""

    if queue_id < 1:
        raise ValueError(
            "queue_id 必須大於 0"
        )

    normalized_status = (
        normalize_enum_value(
            status,
            DividendReviewStatus,
            "status",
        )
    )

    if normalized_status is None:
        raise ValueError(
            "status 不得為空白"
        )

    if changed_at is None:
        changed_at = datetime.now(
            timezone.utc
        )

    if changed_at.tzinfo is None:
        raise ValueError(
            "changed_at 必須包含時區"
        )

    normalized_notes = (
        notes.strip()
        if notes
        else None
    )

    resolved_at = (
        changed_at.isoformat()
        if (
            normalized_status
            == DividendReviewStatus.RESOLVED.value
        )
        else None
    )

    connection = get_connection(
        database_path
    )

    try:
        cursor = connection.execute(
            """
            UPDATE dividend_source_review_queue
            SET
                status = ?,
                notes = ?,
                resolution_document_id = ?,
                resolved_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (
                normalized_status,
                normalized_notes,
                resolution_document_id,
                resolved_at,
                queue_id,
            ),
        )

        if cursor.rowcount != 1:
            raise KeyError(
                "找不到審核佇列項目："
                f"{queue_id}"
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _suggest_source_id(
    event: dict[str, Any],
    issue_type: DividendReviewIssueType,
) -> str:
    """依現有稽核資訊建立保守的建議來源。"""

    if (
        issue_type
        == (
            DividendReviewIssueType
            .MISSING_SOURCE_DOCUMENT
        )
        and event["actual_source_ids"]
    ):
        return (
            str(
                event["actual_source_ids"]
            )
            .split(",", 1)[0]
            .strip()
            .lower()
        )

    return (
        "manual_actual_dividend_notice"
    )


def synchronize_dividend_review_queue(
    database_path: str | Path | None = None,
    run_at: datetime | None = None,
) -> DividendReviewQueueSyncSummary:
    """依即時覆蓋狀態建立、重開或解決佇列。"""

    if run_at is None:
        run_at = datetime.now(
            timezone.utc
        )

    if run_at.tzinfo is None:
        raise ValueError(
            "run_at 必須包含時區"
        )

    evaluated_at = run_at.isoformat()

    connection = get_connection(
        database_path
    )

    created_count = 0
    reopened_count = 0
    resolved_count = 0
    unchanged_count = 0

    try:
        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        events = (
            _fetch_dividend_coverage_events(
                connection
            )
        )

        existing_rows = connection.execute(
            """
            SELECT *
            FROM dividend_source_review_queue;
            """
        ).fetchall()

        existing = {
            (
                int(row["dividend_id"]),
                row["issue_type"],
            ): dict(row)
            for row in existing_rows
        }

        missing_keys: set[
            tuple[int, str]
        ] = set()

        for event in events:
            issue_types: list[
                DividendReviewIssueType
            ] = []

            if not event[
                "has_actual_components"
            ]:
                issue_types.append(
                    DividendReviewIssueType
                    .MISSING_ACTUAL_COMPONENTS
                )

            if not event[
                "has_source_document"
            ]:
                issue_types.append(
                    DividendReviewIssueType
                    .MISSING_SOURCE_DOCUMENT
                )

            for issue_type in issue_types:
                key = (
                    int(event["dividend_id"]),
                    issue_type.value,
                )

                missing_keys.add(
                    key
                )

                suggested_source_id = (
                    _suggest_source_id(
                        event,
                        issue_type,
                    )
                )

                priority = (
                    10
                    if (
                        issue_type
                        == (
                            DividendReviewIssueType
                            .MISSING_ACTUAL_COMPONENTS
                        )
                    )
                    else 20
                )

                row = existing.get(
                    key
                )

                if row is None:
                    connection.execute(
                        """
                        INSERT INTO
                        dividend_source_review_queue (
                            dividend_id,
                            issue_type,
                            suggested_source_id,
                            priority,
                            status,
                            last_evaluated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?);
                        """,
                        (
                            event["dividend_id"],
                            issue_type.value,
                            suggested_source_id,
                            priority,
                            (
                                DividendReviewStatus
                                .PENDING
                                .value
                            ),
                            evaluated_at,
                        ),
                    )

                    created_count += 1
                    continue

                if (
                    row["status"]
                    == (
                        DividendReviewStatus
                        .RESOLVED
                        .value
                    )
                ):
                    connection.execute(
                        """
                        UPDATE dividend_source_review_queue
                        SET
                            suggested_source_id = ?,
                            priority = ?,
                            status = 'PENDING',
                            resolution_document_id = NULL,
                            resolved_at = NULL,
                            last_evaluated_at = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?;
                        """,
                        (
                            suggested_source_id,
                            priority,
                            evaluated_at,
                            row["id"],
                        ),
                    )

                    reopened_count += 1

                else:
                    connection.execute(
                        """
                        UPDATE dividend_source_review_queue
                        SET
                            suggested_source_id = ?,
                            priority = ?,
                            last_evaluated_at = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?;
                        """,
                        (
                            suggested_source_id,
                            priority,
                            evaluated_at,
                            row["id"],
                        ),
                    )

                    unchanged_count += 1

        for key, row in existing.items():
            if key in missing_keys:
                continue

            resolution_document_id = (
                next(
                    (
                        event[
                            "latest_source_document_id"
                        ]
                        for event in events
                        if int(
                            event["dividend_id"]
                        )
                        == key[0]
                    ),
                    None,
                )
            )

            if (
                row["status"]
                != (
                    DividendReviewStatus
                    .RESOLVED
                    .value
                )
            ):
                connection.execute(
                    """
                    UPDATE dividend_source_review_queue
                    SET
                        status = 'RESOLVED',
                        resolution_document_id = ?,
                        resolved_at = ?,
                        last_evaluated_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                    """,
                    (
                        resolution_document_id,
                        evaluated_at,
                        evaluated_at,
                        row["id"],
                    ),
                )

                resolved_count += 1

            else:
                connection.execute(
                    """
                    UPDATE dividend_source_review_queue
                    SET
                        resolution_document_id = COALESCE(
                            ?,
                            resolution_document_id
                        ),
                        last_evaluated_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                    """,
                    (
                        resolution_document_id,
                        evaluated_at,
                        row["id"],
                    ),
                )

                unchanged_count += 1

        connection.commit()

        return DividendReviewQueueSyncSummary(
            evaluated_event_count=len(
                events
            ),
            created_item_count=(
                created_count
            ),
            reopened_item_count=(
                reopened_count
            ),
            resolved_item_count=(
                resolved_count
            ),
            unchanged_item_count=(
                unchanged_count
            ),
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
