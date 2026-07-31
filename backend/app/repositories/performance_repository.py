"""ETF 績效資料 Repository。"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from backend.app.database.connection import (
    get_connection,
)
from backend.app.models.etf_analysis import (
    ETFPerformanceImportRecord,
    PerformanceMetric,
    PerformancePeriod,
)
from backend.app.utils.date_tools import (
    shift_months,
)


@dataclass(
    frozen=True,
    slots=True,
)
class PerformanceCandidate:
    """準備計算績效的 ETF。"""

    code: str
    name: str
    listing_date: date | None


@dataclass(
    frozen=True,
    slots=True,
)
class PerformanceUpsertSummary:
    """ETF 績效 Upsert 結果。"""

    total_records: int
    inserted_records: int
    updated_records: int


def normalize_codes(
    codes: list[str] | tuple[str, ...] | None,
) -> list[str]:
    """正規化 ETF 代號清單。"""

    if not codes:
        return []

    normalized_codes = {
        code.strip().upper()
        for code in codes
        if code.strip()
    }

    return sorted(normalized_codes)


def list_performance_candidates(
    database_path: str | Path | None = None,
    end_date: date | None = None,
    include_bond: bool = False,
    codes: list[str] | tuple[str, ...] | None = None,
    limit: int | None = None,
    minimum_history_months: int = 6,
) -> list[PerformanceCandidate]:
    """取得可計算績效的 ETF 候選清單。

    Args:
        database_path:
            SQLite 資料庫路徑。
        end_date:
            績效計算截止日期。
        include_bond:
            是否包含債券 ETF。
        codes:
            指定 ETF 代號。
        limit:
            最多回傳筆數。
        minimum_history_months:
            候選 ETF 至少需上市的月份數。
            0 代表只要求上市日不晚於截止日。

    Returns:
        list[PerformanceCandidate]:
            ETF 候選清單。

    Raises:
        ValueError:
            limit 小於 1。
    """

    if end_date is None:
        end_date = date.today()

    if limit is not None and limit < 1:
        raise ValueError(
            "limit 必須大於 0"
        )

    if minimum_history_months < 0:
        raise ValueError(
            "minimum_history_months "
            "不得小於 0"
        )

    earliest_listing_date = shift_months(
        end_date,
        -minimum_history_months,
    )

    conditions = [
        """
        (
            listing_date IS NULL
            OR listing_date <= ?
        )
        """
    ]

    parameters: list[Any] = [
        earliest_listing_date.isoformat(),
    ]

    if not include_bond:
        conditions.append(
            "is_bond = 0"
        )

    normalized_codes = normalize_codes(
        codes
    )

    if normalized_codes:
        placeholders = ", ".join(
            "?"
            for _ in normalized_codes
        )

        conditions.append(
            f"code IN ({placeholders})"
        )

        parameters.extend(
            normalized_codes
        )

    where_clause = (
        "WHERE "
        + " AND ".join(conditions)
    )

    limit_clause = ""

    if limit is not None:
        limit_clause = "LIMIT ?"
        parameters.append(limit)

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            SELECT
                code,
                name,
                listing_date
            FROM etf_master
            {where_clause}
            ORDER BY code
            {limit_clause};
            """,
            parameters,
        ).fetchall()

        candidates: list[
            PerformanceCandidate
        ] = []

        for row in rows:
            listing_date_value = (
                date.fromisoformat(
                    row["listing_date"]
                )
                if row["listing_date"]
                else None
            )

            candidates.append(
                PerformanceCandidate(
                    code=row["code"],
                    name=row["name"],
                    listing_date=(
                        listing_date_value
                    ),
                )
            )

        return candidates

    finally:
        connection.close()


def validate_unique_performance_keys(
    records: list[
        ETFPerformanceImportRecord
    ],
) -> None:
    """確認同一批績效資料沒有重複鍵值。"""

    seen_keys: set[
        tuple[str, str, str, str, str]
    ] = set()

    duplicate_keys: set[
        tuple[str, str, str, str, str]
    ] = set()

    for record in records:
        key = (
            record.etf_code,
            record.as_of_date.isoformat(),
            record.period_code.value,
            record.metric_code.value,
            record.source_id,
        )

        if key in seen_keys:
            duplicate_keys.add(key)

        seen_keys.add(key)

    if duplicate_keys:
        duplicate_text = "; ".join(
            "/".join(key)
            for key in sorted(
                duplicate_keys
            )
        )

        raise ValueError(
            "績效匯入資料包含重複鍵值："
            f"{duplicate_text}"
        )


def upsert_performance_records(
    records: list[
        ETFPerformanceImportRecord
    ],
    database_path: str | Path | None = None,
) -> PerformanceUpsertSummary:
    """新增或更新 ETF 績效資料。"""

    validate_unique_performance_keys(
        records
    )

    if not records:
        return PerformanceUpsertSummary(
            total_records=0,
            inserted_records=0,
            updated_records=0,
        )

    connection = get_connection(
        database_path
    )

    try:
        existing_rows = connection.execute(
            """
            SELECT
                etf_code,
                as_of_date,
                period_code,
                metric_code,
                source_id
            FROM etf_performance;
            """
        ).fetchall()

        existing_keys = {
            (
                row["etf_code"],
                row["as_of_date"],
                row["period_code"],
                row["metric_code"],
                row["source_id"],
            )
            for row in existing_rows
        }

        incoming_keys = {
            (
                record.etf_code,
                record.as_of_date.isoformat(),
                record.period_code.value,
                record.metric_code.value,
                record.source_id,
            )
            for record in records
        }

        inserted_records = len(
            incoming_keys - existing_keys
        )

        updated_records = len(
            incoming_keys & existing_keys
        )

        connection.executemany(
            """
            INSERT INTO etf_performance (
                etf_code,
                as_of_date,
                period_code,
                metric_code,
                return_pct,
                source_id,
                import_batch_id,
                source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (
                etf_code,
                as_of_date,
                period_code,
                metric_code,
                source_id
            )
            DO UPDATE SET
                return_pct =
                    excluded.return_pct,
                import_batch_id =
                    excluded.import_batch_id,
                source_updated_at =
                    excluded.source_updated_at,
                updated_at =
                    CURRENT_TIMESTAMP;
            """,
            [
                (
                    record.etf_code,
                    record.as_of_date.isoformat(),
                    record.period_code.value,
                    record.metric_code.value,
                    float(record.return_pct),
                    record.source_id,
                    record.import_batch_id,
                    (
                        record.source_updated_at
                        .isoformat()
                        if record.source_updated_at
                        else None
                    ),
                )
                for record in records
            ],
        )

        connection.commit()

        return PerformanceUpsertSummary(
            total_records=len(records),
            inserted_records=(
                inserted_records
            ),
            updated_records=(
                updated_records
            ),
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_latest_performance_ranking(
    database_path: str | Path | None = None,
    period_code: PerformancePeriod = (
        PerformancePeriod.SIX_MONTHS
    ),
    metric_code: PerformanceMetric = (
        PerformanceMetric.PRICE_RETURN
    ),
    source_id: str = "twse_stock_day",
    is_active: bool | None = None,
    is_bond: bool | None = False,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """取得各 ETF 最新績效排行榜。

    每檔 ETF 只取最新基準日的一筆資料。
    """

    if limit < 1:
        raise ValueError(
            "limit 必須大於 0"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    conditions = [
        "p.period_code = ?",
        "p.metric_code = ?",
        "p.source_id = ?",
    ]

    parameters: list[Any] = [
        period_code.value,
        metric_code.value,
        source_id.strip().lower(),
    ]

    if is_active is not None:
        conditions.append(
            "m.is_active = ?"
        )

        parameters.append(
            int(is_active)
        )

    if is_bond is not None:
        conditions.append(
            "m.is_bond = ?"
        )

        parameters.append(
            int(is_bond)
        )

    where_clause = (
        " AND ".join(conditions)
    )

    parameters.extend(
        [
            limit,
            offset,
        ]
    )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            WITH ranked_performance AS (
                SELECT
                    p.etf_code,
                    m.name,
                    m.is_active,
                    m.is_bond,
                    p.as_of_date,
                    p.period_code,
                    p.metric_code,
                    p.return_pct,
                    p.source_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.etf_code
                        ORDER BY
                            p.as_of_date DESC,
                            p.id DESC
                    ) AS row_number
                FROM etf_performance AS p
                INNER JOIN etf_master AS m
                    ON m.code = p.etf_code
                WHERE {where_clause}
            )
            SELECT
                etf_code,
                name,
                is_active,
                is_bond,
                as_of_date,
                period_code,
                metric_code,
                return_pct,
                source_id
            FROM ranked_performance
            WHERE row_number = 1
            ORDER BY
                return_pct DESC,
                etf_code
            LIMIT ?
            OFFSET ?;
            """,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def count_latest_performance_ranking(
    database_path: str | Path | None = None,
    period_code: PerformancePeriod = (
        PerformancePeriod.SIX_MONTHS
    ),
    metric_code: PerformanceMetric = (
        PerformanceMetric.PRICE_RETURN
    ),
    source_id: str = "twse_stock_day",
    is_active: bool | None = None,
    is_bond: bool | None = False,
) -> int:
    """計算排行榜 ETF 總數。"""

    conditions = [
        "p.period_code = ?",
        "p.metric_code = ?",
        "p.source_id = ?",
    ]

    parameters: list[Any] = [
        period_code.value,
        metric_code.value,
        source_id.strip().lower(),
    ]

    if is_active is not None:
        conditions.append(
            "m.is_active = ?"
        )

        parameters.append(
            int(is_active)
        )

    if is_bond is not None:
        conditions.append(
            "m.is_bond = ?"
        )

        parameters.append(
            int(is_bond)
        )

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            f"""
            SELECT
                COUNT(
                    DISTINCT p.etf_code
                ) AS total
            FROM etf_performance AS p
            INNER JOIN etf_master AS m
                ON m.code = p.etf_code
            WHERE {" AND ".join(conditions)};
            """,
            parameters,
        ).fetchone()

        return int(row["total"])

    finally:
        connection.close()
MULTI_PERIOD_RANKING_PERIODS = (
    PerformancePeriod.ONE_MONTH,
    PerformancePeriod.THREE_MONTHS,
    PerformancePeriod.SIX_MONTHS,
    PerformancePeriod.ONE_YEAR,
)


def list_latest_multi_period_performance_ranking(
    database_path: str | Path | None = None,
    sort_period: PerformancePeriod = (
        PerformancePeriod.SIX_MONTHS
    ),
    metric_code: PerformanceMetric = (
        PerformanceMetric.PRICE_RETURN
    ),
    source_id: str = "twse_stock_day",
    is_active: bool | None = None,
    is_bond: bool | None = False,
    limit: int = 20,
    offset: int = 0,
    period_codes: tuple[
        PerformancePeriod,
        ...,
    ] = MULTI_PERIOD_RANKING_PERIODS,
) -> list[dict[str, Any]]:
    """依一個主要期間排序，同時回傳各 ETF 多期間績效。

    排名只使用 ``sort_period``。1M、3M、6M、1Y
    仍各自保留最新紀錄；缺少期間不會建立零值。
    """

    if limit < 1:
        raise ValueError(
            "limit 必須大於 0"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    normalized_sort_period = (
        PerformancePeriod(
            sort_period
        )
    )

    normalized_periods = tuple(
        dict.fromkeys(
            PerformancePeriod(
                period_code
            )
            for period_code in period_codes
        )
    )

    if (
        normalized_sort_period
        not in normalized_periods
    ):
        raise ValueError(
            "sort_period 必須包含在 period_codes"
        )

    normalized_source_id = (
        source_id.strip().lower()
    )

    if not normalized_source_id:
        raise ValueError(
            "source_id 不得為空白"
        )

    placeholders = ", ".join(
        "?"
        for _ in normalized_periods
    )

    filters = [
        "latest.row_number = 1",
        "latest.period_code = ?",
    ]

    parameters: list[Any] = [
        metric_code.value,
        normalized_source_id,
        *(
            period.value
            for period in normalized_periods
        ),
        normalized_sort_period.value,
    ]

    if is_active is not None:
        filters.append(
            "master.is_active = ?"
        )
        parameters.append(
            int(is_active)
        )

    if is_bond is not None:
        filters.append(
            "master.is_bond = ?"
        )
        parameters.append(
            int(is_bond)
        )

    parameters.extend(
        [
            limit,
            offset,
        ]
    )

    period_order_sql = " ".join(
        (
            "WHEN "
            f"'{period.value}' "
            f"THEN {index}"
        )
        for index, period in enumerate(
            normalized_periods,
            start=1,
        )
    )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            WITH latest_performance AS (
                SELECT
                    p.etf_code,
                    p.as_of_date,
                    p.period_code,
                    p.metric_code,
                    p.return_pct,
                    p.source_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            p.etf_code,
                            p.period_code
                        ORDER BY
                            p.as_of_date DESC,
                            p.id DESC
                    ) AS row_number
                FROM etf_performance AS p
                WHERE
                    p.metric_code = ?
                    AND p.source_id = ?
                    AND p.period_code IN (
                        {placeholders}
                    )
            ),
            selected_etfs AS (
                SELECT
                    latest.etf_code,
                    master.name,
                    master.is_active,
                    master.is_bond,
                    latest.as_of_date
                        AS sort_as_of_date,
                    latest.return_pct
                        AS sort_return_pct,
                    latest.source_id
                        AS sort_source_id
                FROM latest_performance
                    AS latest
                INNER JOIN etf_master
                    AS master
                    ON master.code =
                        latest.etf_code
                WHERE {" AND ".join(filters)}
                ORDER BY
                    latest.return_pct DESC,
                    latest.etf_code
                LIMIT ?
                OFFSET ?
            )
            SELECT
                selected.etf_code,
                selected.name,
                selected.is_active,
                selected.is_bond,
                selected.sort_as_of_date,
                selected.sort_return_pct,
                selected.sort_source_id,
                period.as_of_date,
                period.period_code,
                period.metric_code,
                period.return_pct,
                period.source_id
                    AS period_source_id
            FROM selected_etfs AS selected
            LEFT JOIN latest_performance
                AS period
                ON period.etf_code =
                    selected.etf_code
                AND period.row_number = 1
            ORDER BY
                selected.sort_return_pct DESC,
                selected.etf_code,
                CASE period.period_code
                    {period_order_sql}
                    ELSE 99
                END;
            """,
            parameters,
        ).fetchall()

        results: list[
            dict[str, Any]
        ] = []

        result_by_code: dict[
            str,
            dict[str, Any],
        ] = {}

        for row in rows:
            code = str(
                row["etf_code"]
            )

            result = result_by_code.get(
                code
            )

            if result is None:
                result = {
                    "etf_code": code,
                    "name": row["name"],
                    "is_active": bool(
                        row["is_active"]
                    ),
                    "is_bond": bool(
                        row["is_bond"]
                    ),
                    "sort_period": (
                        normalized_sort_period.value
                    ),
                    "sort_as_of_date": (
                        row["sort_as_of_date"]
                    ),
                    "sort_return_pct": float(
                        row["sort_return_pct"]
                    ),
                    "source_id": (
                        row["sort_source_id"]
                    ),
                    "performance_items": [],
                }

                result_by_code[code] = (
                    result
                )
                results.append(result)

            if row["period_code"] is None:
                continue

            result[
                "performance_items"
            ].append(
                {
                    "as_of_date": (
                        row["as_of_date"]
                    ),
                    "period_code": (
                        row["period_code"]
                    ),
                    "metric_code": (
                        row["metric_code"]
                    ),
                    "return_pct": float(
                        row["return_pct"]
                    ),
                    "source_id": (
                        row[
                            "period_source_id"
                        ]
                    ),
                }
            )

        return results

    finally:
        connection.close()


DEFAULT_ETF_PERFORMANCE_PERIODS = (
    *MULTI_PERIOD_RANKING_PERIODS,
)


def list_latest_etf_performance(
    etf_code: str,
    database_path: str | Path | None = None,
    metric_code: PerformanceMetric = (
        PerformanceMetric.PRICE_RETURN
    ),
    source_id: str = "twse_stock_day",
    period_codes: tuple[
        PerformancePeriod,
        ...,
    ] = DEFAULT_ETF_PERFORMANCE_PERIODS,
) -> list[dict[str, Any]]:
    """取得單一 ETF 各期間的最新績效。

    每個期間只回傳最新基準日的一筆資料，
    並依傳入的期間順序排列。
    """

    normalized_code = (
        etf_code.strip().upper()
    )

    if not normalized_code:
        raise ValueError(
            "etf_code 不得為空白"
        )

    normalized_periods = tuple(
        dict.fromkeys(
            PerformancePeriod(
                period_code
            )
            for period_code in period_codes
        )
    )

    if not normalized_periods:
        return []

    placeholders = ", ".join(
        "?"
        for _ in normalized_periods
    )

    parameters: list[Any] = [
        normalized_code,
        metric_code.value,
        source_id.strip().lower(),
        *(
            period.value
            for period in normalized_periods
        ),
    ]

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            WITH ranked_performance AS (
                SELECT
                    p.as_of_date,
                    p.period_code,
                    p.metric_code,
                    p.return_pct,
                    p.source_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            p.period_code
                        ORDER BY
                            p.as_of_date DESC,
                            p.id DESC
                    ) AS row_number
                FROM etf_performance AS p
                WHERE
                    p.etf_code = ?
                    AND p.metric_code = ?
                    AND p.source_id = ?
                    AND p.period_code IN (
                        {placeholders}
                    )
            )
            SELECT
                as_of_date,
                period_code,
                metric_code,
                return_pct,
                source_id
            FROM ranked_performance
            WHERE row_number = 1;
            """,
            parameters,
        ).fetchall()

        order_by_period = {
            period.value: index
            for index, period in enumerate(
                normalized_periods
            )
        }

        results = [
            dict(row)
            for row in rows
        ]

        results.sort(
            key=lambda row: (
                order_by_period[
                    row["period_code"]
                ]
            )
        )

        return results

    finally:
        connection.close()
