"""ETF 詳細頁資料來源與新鮮度 Repository。"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sqlite3

from backend.app.data_sources.actual_dividend_source_registry import (
    get_actual_dividend_source,
)
from backend.app.data_sources.registry import (
    get_data_source,
)
from backend.app.database.connection import (
    get_connection,
)


PROFILE_PERIODS = (
    "1M",
    "3M",
    "6M",
    "1Y",
)

PROFILE_METRIC = "PRICE_RETURN"


def _source_display_name(
    source_id: str,
) -> str:
    """將來源識別碼轉為可讀名稱。"""

    normalized_source_id = (
        source_id.strip().lower()
    )

    try:
        return get_data_source(
            normalized_source_id
        ).display_name

    except KeyError:
        pass

    try:
        return get_actual_dividend_source(
            normalized_source_id
        ).issuer_name

    except KeyError:
        return normalized_source_id


def _build_source_references(
    source_ids: list[str],
) -> list[dict[str, str]]:
    """建立排序且去重的來源顯示資料。"""

    normalized_ids = sorted(
        {
            source_id.strip().lower()
            for source_id in source_ids
            if source_id.strip()
        }
    )

    return [
        {
            "source_id": source_id,
            "display_name": (
                _source_display_name(
                    source_id
                )
            ),
        }
        for source_id in normalized_ids
    ]


def _read_source_ids(
    connection: sqlite3.Connection,
    query: str,
    parameters: tuple[Any, ...],
) -> list[str]:
    """執行只回傳 source_id 的查詢。"""

    rows = connection.execute(
        query,
        parameters,
    ).fetchall()

    return [
        str(row["source_id"])
        for row in rows
        if row["source_id"]
    ]


def _read_master_profile(
    connection: sqlite3.Connection,
) -> dict[str, Any]:
    """讀取 ETF 主資料資料集更新狀態。"""

    row = connection.execute(
        """
        SELECT MAX(completed_at)
            AS latest_import_at
        FROM import_batch
        WHERE pipeline_name = ?
          AND status = 'success';
        """,
        (
            "etf_master_pipeline",
        ),
    ).fetchone()

    return {
        "sources": (
            _build_source_references(
                ["twse_openapi"]
            )
        ),
        "latest_import_at": (
            row["latest_import_at"]
        ),
    }


def _read_performance_profile(
    connection: sqlite3.Connection,
    etf_code: str,
) -> dict[str, Any]:
    """讀取單一 ETF 的市價績效新鮮度。"""

    row = connection.execute(
        """
        SELECT
            COUNT(*) AS record_count,
            MAX(p.as_of_date)
                AS latest_as_of_date,
            MAX(ib.completed_at)
                AS latest_import_at
        FROM etf_performance AS p
        LEFT JOIN import_batch AS ib
            ON ib.id = p.import_batch_id
        WHERE p.etf_code = ?
          AND p.metric_code = ?
          AND p.period_code IN (
              '1M',
              '3M',
              '6M',
              '1Y'
          );
        """,
        (
            etf_code,
            PROFILE_METRIC,
        ),
    ).fetchone()

    period_rows = connection.execute(
        """
        SELECT DISTINCT period_code
        FROM etf_performance
        WHERE etf_code = ?
          AND metric_code = ?
          AND period_code IN (
              '1M',
              '3M',
              '6M',
              '1Y'
          );
        """,
        (
            etf_code,
            PROFILE_METRIC,
        ),
    ).fetchall()

    available_periods = [
        period_code
        for period_code in PROFILE_PERIODS
        if period_code in {
            row["period_code"]
            for row in period_rows
        }
    ]

    source_ids = _read_source_ids(
        connection,
        """
        SELECT DISTINCT source_id
        FROM etf_performance
        WHERE etf_code = ?
          AND metric_code = ?
          AND period_code IN (
              '1M',
              '3M',
              '6M',
              '1Y'
          )
        ORDER BY source_id;
        """,
        (
            etf_code,
            PROFILE_METRIC,
        ),
    )

    return {
        "metric_code": PROFILE_METRIC,
        "sources": (
            _build_source_references(
                source_ids
            )
        ),
        "record_count": int(
            row["record_count"]
        ),
        "available_periods": (
            available_periods
        ),
        "latest_as_of_date": (
            row["latest_as_of_date"]
        ),
        "latest_import_at": (
            row["latest_import_at"]
        ),
    }


def _read_dividend_profile(
    connection: sqlite3.Connection,
    etf_code: str,
) -> dict[str, Any]:
    """讀取單一 ETF 的配息事件新鮮度。"""

    row = connection.execute(
        """
        SELECT
            COUNT(*) AS event_count,
            MAX(ib.completed_at)
                AS latest_import_at
        FROM etf_dividend AS d
        LEFT JOIN import_batch AS ib
            ON ib.id = d.import_batch_id
        WHERE d.etf_code = ?;
        """,
        (
            etf_code,
        ),
    ).fetchone()

    latest_date_row = connection.execute(
        """
        SELECT MAX(event_date)
            AS latest_event_date
        FROM (
            SELECT announcement_date
                AS event_date
            FROM etf_dividend
            WHERE etf_code = ?
              AND announcement_date
                  IS NOT NULL

            UNION ALL

            SELECT ex_dividend_date
            FROM etf_dividend
            WHERE etf_code = ?
              AND ex_dividend_date
                  IS NOT NULL

            UNION ALL

            SELECT record_date
            FROM etf_dividend
            WHERE etf_code = ?
              AND record_date
                  IS NOT NULL

            UNION ALL

            SELECT payment_date
            FROM etf_dividend
            WHERE etf_code = ?
              AND payment_date
                  IS NOT NULL
        );
        """,
        (
            etf_code,
            etf_code,
            etf_code,
            etf_code,
        ),
    ).fetchone()

    source_ids = _read_source_ids(
        connection,
        """
        SELECT DISTINCT source_id
        FROM etf_dividend
        WHERE etf_code = ?
        ORDER BY source_id;
        """,
        (
            etf_code,
        ),
    )

    return {
        "sources": (
            _build_source_references(
                source_ids
            )
        ),
        "event_count": int(
            row["event_count"]
        ),
        "latest_event_date": (
            latest_date_row[
                "latest_event_date"
            ]
        ),
        "latest_import_at": (
            row["latest_import_at"]
        ),
    }


def _read_actual_dividend_profile(
    connection: sqlite3.Connection,
    etf_code: str,
) -> dict[str, Any]:
    """讀取正式配息組成與來源文件新鮮度。"""

    count_row = connection.execute(
        """
        SELECT
            COUNT(
                DISTINCT CASE
                    WHEN c.component_basis = 'ACTUAL'
                    THEN d.id
                END
            ) AS actual_component_event_count,
            COUNT(
                DISTINCT CASE
                    WHEN c.component_basis = 'ACTUAL'
                     AND c.component_code = '76W'
                    THEN d.id
                END
            ) AS actual_76w_event_count,
            MAX(
                CASE
                    WHEN c.component_basis = 'ACTUAL'
                    THEN ib.completed_at
                END
            ) AS latest_import_at
        FROM etf_dividend AS d
        LEFT JOIN etf_dividend_component AS c
            ON c.dividend_id = d.id
        LEFT JOIN import_batch AS ib
            ON ib.id = c.import_batch_id
        WHERE d.etf_code = ?;
        """,
        (
            etf_code,
        ),
    ).fetchone()

    document_row = connection.execute(
        """
        SELECT
            COUNT(
                DISTINCT d.id
            ) AS source_document_event_count,
            MAX(sd.source_document_date)
                AS latest_source_document_date
        FROM etf_dividend AS d
        INNER JOIN etf_dividend_component AS c
            ON c.dividend_id = d.id
           AND c.component_basis = 'ACTUAL'
        INNER JOIN dividend_source_document AS sd
            ON sd.import_batch_id = c.import_batch_id
           AND sd.parse_status = 'parsed'
           AND sd.information_basis = 'ACTUAL'
        WHERE d.etf_code = ?;
        """,
        (
            etf_code,
        ),
    ).fetchone()

    component_sources = _read_source_ids(
        connection,
        """
        SELECT DISTINCT c.source_id
        FROM etf_dividend AS d
        INNER JOIN etf_dividend_component AS c
            ON c.dividend_id = d.id
        WHERE d.etf_code = ?
          AND c.component_basis = 'ACTUAL'
        ORDER BY c.source_id;
        """,
        (
            etf_code,
        ),
    )

    document_sources = _read_source_ids(
        connection,
        """
        SELECT DISTINCT sd.source_id
        FROM etf_dividend AS d
        INNER JOIN etf_dividend_component AS c
            ON c.dividend_id = d.id
           AND c.component_basis = 'ACTUAL'
        INNER JOIN dividend_source_document AS sd
            ON sd.import_batch_id = c.import_batch_id
           AND sd.parse_status = 'parsed'
           AND sd.information_basis = 'ACTUAL'
        WHERE d.etf_code = ?
        ORDER BY sd.source_id;
        """,
        (
            etf_code,
        ),
    )

    return {
        "sources": (
            _build_source_references(
                [
                    *component_sources,
                    *document_sources,
                ]
            )
        ),
        "actual_component_event_count": int(
            count_row[
                "actual_component_event_count"
            ]
        ),
        "actual_76w_event_count": int(
            count_row[
                "actual_76w_event_count"
            ]
        ),
        "source_document_event_count": int(
            document_row[
                "source_document_event_count"
            ]
        ),
        "latest_source_document_date": (
            document_row[
                "latest_source_document_date"
            ]
        ),
        "latest_import_at": (
            count_row["latest_import_at"]
        ),
    }


def build_etf_data_profile(
    etf_code: str,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """建立單一 ETF 的資料來源與新鮮度摘要。"""

    normalized_code = (
        etf_code.strip().upper()
    )

    if not normalized_code:
        return None

    connection = get_connection(
        database_path
    )

    try:
        etf = connection.execute(
            """
            SELECT code
            FROM etf_master
            WHERE code = ?;
            """,
            (
                normalized_code,
            ),
        ).fetchone()

        if etf is None:
            return None

        return {
            "etf_code": normalized_code,
            "master": (
                _read_master_profile(
                    connection
                )
            ),
            "performance": (
                _read_performance_profile(
                    connection,
                    normalized_code,
                )
            ),
            "dividends": (
                _read_dividend_profile(
                    connection,
                    normalized_code,
                )
            ),
            "actual_dividend": (
                _read_actual_dividend_profile(
                    connection,
                    normalized_code,
                )
            ),
        }

    finally:
        connection.close()
