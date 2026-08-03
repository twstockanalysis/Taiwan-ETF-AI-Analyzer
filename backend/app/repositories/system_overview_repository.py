"""首頁系統資料總覽 Repository。"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sqlite3

from backend.app.database.connection import (
    get_connection,
)


OVERVIEW_PERFORMANCE_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)

OVERVIEW_PERFORMANCE_METRIC = (
    "PRICE_RETURN"
)

OVERVIEW_PERFORMANCE_SOURCE = (
    "twse_stock_day"
)


def calculate_coverage_pct(
    covered_count: int,
    total_count: int,
) -> float | None:
    """計算首頁覆蓋率並保留零分母語意。"""

    if total_count == 0:
        return None

    return round(
        covered_count
        / total_count
        * 100,
        6,
    )


def _read_etf_overview(
    connection: sqlite3.Connection,
) -> dict[str, Any]:
    """使用既有連線讀取 ETF 主資料摘要。"""

    row = connection.execute(
        """
        SELECT
            COUNT(*) AS total_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN is_active = 1
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS active_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN is_active = 0
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS passive_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN is_bond = 1
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS bond_count,
            COALESCE(
                SUM(
                    CASE
                        WHEN is_bond = 0
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS non_bond_count
        FROM etf_master;
        """
    ).fetchone()

    import_row = connection.execute(
        """
        SELECT
            MAX(completed_at)
                AS latest_master_import_at
        FROM import_batch
        WHERE pipeline_name = ?
          AND status = 'success';
        """,
        (
            "etf_master_pipeline",
        ),
    ).fetchone()

    return {
        "total_count": int(
            row["total_count"]
        ),
        "active_count": int(
            row["active_count"]
        ),
        "passive_count": int(
            row["passive_count"]
        ),
        "bond_count": int(
            row["bond_count"]
        ),
        "non_bond_count": int(
            row["non_bond_count"]
        ),
        "latest_master_import_at": (
            import_row[
                "latest_master_import_at"
            ]
        ),
    }


def _read_performance_overview(
    connection: sqlite3.Connection,
    total_etf_count: int,
) -> dict[str, Any]:
    """使用既有連線讀取市價績效覆蓋摘要。"""

    overall_row = connection.execute(
        """
        SELECT
            COUNT(
                DISTINCT etf_code
            ) AS etf_count,
            MAX(as_of_date)
                AS latest_as_of_date
        FROM etf_performance
        WHERE metric_code = ?
          AND source_id = ?;
        """,
        (
            OVERVIEW_PERFORMANCE_METRIC,
            OVERVIEW_PERFORMANCE_SOURCE,
        ),
    ).fetchone()

    period_rows = connection.execute(
        """
        SELECT
            period_code,
            COUNT(
                DISTINCT etf_code
            ) AS etf_count,
            MAX(as_of_date)
                AS latest_as_of_date
        FROM etf_performance
        WHERE metric_code = ?
          AND source_id = ?
          AND period_code IN (
              '1M',
              '3M',
              '6M',
              '1Y'
          )
        GROUP BY period_code;
        """,
        (
            OVERVIEW_PERFORMANCE_METRIC,
            OVERVIEW_PERFORMANCE_SOURCE,
        ),
    ).fetchall()

    period_lookup = {
        row["period_code"]: dict(row)
        for row in period_rows
    }

    periods: list[
        dict[str, Any]
    ] = []

    for period_code in (
        OVERVIEW_PERFORMANCE_PERIODS
    ):
        row = period_lookup.get(
            period_code
        )

        etf_count = (
            int(row["etf_count"])
            if row is not None
            else 0
        )

        periods.append(
            {
                "period_code": (
                    period_code
                ),
                "etf_count": etf_count,
                "coverage_pct": (
                    calculate_coverage_pct(
                        etf_count,
                        total_etf_count,
                    )
                ),
                "latest_as_of_date": (
                    row["latest_as_of_date"]
                    if row is not None
                    else None
                ),
            }
        )

    etf_count = int(
        overall_row["etf_count"]
    )

    return {
        "metric_code": (
            OVERVIEW_PERFORMANCE_METRIC
        ),
        "source_id": (
            OVERVIEW_PERFORMANCE_SOURCE
        ),
        "etf_count": etf_count,
        "total_etf_count": (
            total_etf_count
        ),
        "coverage_pct": (
            calculate_coverage_pct(
                etf_count,
                total_etf_count,
            )
        ),
        "latest_as_of_date": (
            overall_row[
                "latest_as_of_date"
            ]
        ),
        "periods": periods,
    }


def _read_dividend_overview(
    connection: sqlite3.Connection,
) -> dict[str, Any]:
    """使用既有連線讀取配息與正式資料摘要。"""

    row = connection.execute(
        """
        SELECT
            COUNT(*) AS event_count,
            COUNT(
                DISTINCT d.etf_code
            ) AS etf_count,

            COALESCE(
                SUM(
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM
                                etf_dividend_component
                                AS c
                            WHERE
                                c.dividend_id = d.id
                                AND
                                c.component_basis =
                                'ACTUAL'
                        )
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS
                actual_component_event_count,

            COALESCE(
                SUM(
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM
                                etf_dividend_component
                                AS c
                            WHERE
                                c.dividend_id = d.id
                                AND
                                c.component_basis =
                                'ACTUAL'
                                AND
                                c.component_code =
                                '76W'
                        )
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS actual_76w_event_count,

            COALESCE(
                SUM(
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM
                                etf_dividend_component
                                AS c
                            INNER JOIN
                                dividend_source_document
                                AS sd
                                ON
                                sd.import_batch_id =
                                c.import_batch_id
                            WHERE
                                c.dividend_id = d.id
                                AND
                                c.component_basis =
                                'ACTUAL'
                                AND
                                sd.parse_status =
                                'parsed'
                                AND
                                sd.information_basis =
                                'ACTUAL'
                        )
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS
                source_document_event_count
        FROM etf_dividend AS d;
        """
    ).fetchone()

    latest_event_row = connection.execute(
        """
        SELECT
            MAX(event_date)
                AS latest_event_date
        FROM (
            SELECT announcement_date
                AS event_date
            FROM etf_dividend
            WHERE announcement_date
                IS NOT NULL

            UNION ALL

            SELECT ex_dividend_date
            FROM etf_dividend
            WHERE ex_dividend_date
                IS NOT NULL

            UNION ALL

            SELECT record_date
            FROM etf_dividend
            WHERE record_date
                IS NOT NULL

            UNION ALL

            SELECT payment_date
            FROM etf_dividend
            WHERE payment_date
                IS NOT NULL
        );
        """
    ).fetchone()

    source_row = connection.execute(
        """
        SELECT
            MAX(source_document_date)
                AS latest_source_document_date
        FROM dividend_source_document
        WHERE parse_status = 'parsed'
          AND information_basis = 'ACTUAL';
        """
    ).fetchone()

    event_count = int(
        row["event_count"]
    )

    actual_count = int(
        row[
            "actual_component_event_count"
        ]
    )

    actual_76w_count = int(
        row[
            "actual_76w_event_count"
        ]
    )

    source_document_count = int(
        row[
            "source_document_event_count"
        ]
    )

    return {
        "event_count": event_count,
        "etf_count": int(
            row["etf_count"]
        ),
        "latest_event_date": (
            latest_event_row[
                "latest_event_date"
            ]
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
        "actual_component_coverage_pct": (
            calculate_coverage_pct(
                actual_count,
                event_count,
            )
        ),
        "actual_76w_coverage_pct": (
            calculate_coverage_pct(
                actual_76w_count,
                event_count,
            )
        ),
        "source_document_coverage_pct": (
            calculate_coverage_pct(
                source_document_count,
                event_count,
            )
        ),
        (
            "latest_actual_"
            "source_document_date"
        ): (
            source_row[
                "latest_source_document_date"
            ]
        ),
    }


def _read_recent_import_batches(
    connection: sqlite3.Connection,
    limit: int,
) -> list[dict[str, Any]]:
    """使用既有連線取得最近匯入批次。"""

    rows = connection.execute(
        """
        SELECT
            id AS batch_id,
            pipeline_name,
            source_id,
            endpoint_id,
            started_at,
            completed_at,
            status,
            raw_record_count,
            accepted_record_count,
            rejected_record_count,
            inserted_record_count,
            updated_record_count,
            error_message
        FROM import_batch
        ORDER BY id DESC
        LIMIT ?;
        """,
        (
            limit,
        ),
    ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def build_system_overview(
    database_path: str | Path | None = None,
    *,
    recent_batch_limit: int = 5,
) -> dict[str, Any]:
    """建立首頁需要的單一系統資料總覽。"""

    if (
        recent_batch_limit < 1
        or recent_batch_limit > 20
    ):
        raise ValueError(
            "recent_batch_limit "
            "必須介於 1 到 20"
        )

    connection = get_connection(
        database_path
    )

    try:
        etfs = _read_etf_overview(
            connection
        )

        performance = (
            _read_performance_overview(
                connection,
                total_etf_count=(
                    etfs["total_count"]
                ),
            )
        )

        dividends = (
            _read_dividend_overview(
                connection
            )
        )

        recent_batches = (
            _read_recent_import_batches(
                connection,
                recent_batch_limit,
            )
        )

        return {
            "api_status": "healthy",
            "database_type": "SQLite",
            "etfs": etfs,
            "performance": performance,
            "dividends": dividends,
            "recent_import_batches": (
                recent_batches
            ),
        }

    finally:
        connection.close()
