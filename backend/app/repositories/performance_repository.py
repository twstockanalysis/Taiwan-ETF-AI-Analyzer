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
) -> list[PerformanceCandidate]:
    """取得可計算六個月績效的 ETF。

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

    earliest_listing_date = shift_months(
        end_date,
        -6,
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
        tuple[str, str, str, str]
    ] = set()

    duplicate_keys: set[
        tuple[str, str, str, str]
    ] = set()

    for record in records:
        key = (
            record.etf_code,
            record.as_of_date.isoformat(),
            record.period_code.value,
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
                source_id
            FROM etf_performance;
            """
        ).fetchall()

        existing_keys = {
            (
                row["etf_code"],
                row["as_of_date"],
                row["period_code"],
                row["source_id"],
            )
            for row in existing_rows
        }

        incoming_keys = {
            (
                record.etf_code,
                record.as_of_date.isoformat(),
                record.period_code.value,
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
                return_pct,
                source_id,
                import_batch_id,
                source_updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (
                etf_code,
                as_of_date,
                period_code,
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
        "p.source_id = ?",
    ]

    parameters: list[Any] = [
        period_code.value,
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
    source_id: str = "twse_stock_day",
    is_active: bool | None = None,
    is_bond: bool | None = False,
) -> int:
    """計算排行榜 ETF 總數。"""

    conditions = [
        "p.period_code = ?",
        "p.source_id = ?",
    ]

    parameters: list[Any] = [
        period_code.value,
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