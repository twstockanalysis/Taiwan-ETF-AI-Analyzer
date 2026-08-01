"""ETF dividend event and component Repository."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import sqlite3

from backend.app.database.connection import (
    get_connection,
)
from backend.app.models.etf_analysis import (
    DividendComponentBasis,
    ETFDividendComponentImportRecord,
    ETFDividendImportRecord,
    ETFDividendSummaryMetricRecord,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DividendUpsertSummary:
    """Dividend-event upsert result."""

    total_records: int
    inserted_records: int
    updated_records: int


@dataclass(
    frozen=True,
    slots=True,
)
class DividendComponentUpsertSummary:
    """Dividend-component upsert result."""

    total_records: int
    inserted_records: int
    updated_records: int


@dataclass(
    frozen=True,
    slots=True,
)
class DividendDatasetUpsertSummary:
    """Atomic event-and-component upsert result."""

    dividends: DividendUpsertSummary
    components: DividendComponentUpsertSummary


@dataclass(
    frozen=True,
    slots=True,
)
class DividendSummaryMetricUpsertSummary:
    """配息摘要補充資料 upsert 結果。"""

    total_records: int
    inserted_records: int
    updated_records: int


def _normalize_text(
    value: str,
    field_name: str,
    uppercase: bool = False,
    lowercase: bool = False,
) -> str:
    """Normalize and validate a required text value."""

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(
            f"{field_name} 不得為空白"
        )

    if uppercase:
        normalized_value = (
            normalized_value.upper()
        )

    if lowercase:
        normalized_value = (
            normalized_value.lower()
        )

    return normalized_value


def validate_unique_dividend_keys(
    records: list[
        ETFDividendImportRecord
    ],
) -> None:
    """Reject duplicate dividend keys in one batch."""

    seen_keys: set[
        tuple[str, str]
    ] = set()

    duplicate_keys: set[
        tuple[str, str]
    ] = set()

    for record in records:
        key = (
            record.source_id,
            record.source_event_id,
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
            "配息事件匯入資料包含重複鍵值："
            f"{duplicate_text}"
        )


def validate_unique_component_keys(
    records: list[
        ETFDividendComponentImportRecord
    ],
) -> None:
    """Reject duplicate component keys in one batch."""

    seen_keys: set[
        tuple[str, str, str, str, str]
    ] = set()

    duplicate_keys: set[
        tuple[str, str, str, str, str]
    ] = set()

    for record in records:
        key = (
            record.etf_code,
            record.dividend_source_event_id,
            record.component_basis.value,
            record.component_code,
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
            "配息組成匯入資料包含重複鍵值："
            f"{duplicate_text}"
        )


def _ensure_etf_codes_exist(
    connection: sqlite3.Connection,
    codes: set[str],
) -> None:
    """Raise a clear error when ETF master rows are absent."""

    if not codes:
        return

    placeholders = ", ".join(
        "?"
        for _ in codes
    )

    rows = connection.execute(
        f"""
        SELECT code
        FROM etf_master
        WHERE code IN ({placeholders});
        """,
        sorted(codes),
    ).fetchall()

    existing_codes = {
        row["code"]
        for row in rows
    }

    missing_codes = (
        codes - existing_codes
    )

    if missing_codes:
        raise KeyError(
            "找不到 ETF 主資料："
            + ", ".join(
                sorted(missing_codes)
            )
        )


def _upsert_dividend_records(
    connection: sqlite3.Connection,
    records: list[
        ETFDividendImportRecord
    ],
) -> DividendUpsertSummary:
    """Upsert dividend events using an existing transaction."""

    if not records:
        return DividendUpsertSummary(
            total_records=0,
            inserted_records=0,
            updated_records=0,
        )

    _ensure_etf_codes_exist(
        connection,
        {
            record.etf_code
            for record in records
        },
    )

    existing_rows = connection.execute(
        """
        SELECT
            source_id,
            source_event_id
        FROM etf_dividend;
        """
    ).fetchall()

    existing_keys = {
        (
            row["source_id"],
            row["source_event_id"],
        )
        for row in existing_rows
    }

    incoming_keys = {
        (
            record.source_id,
            record.source_event_id,
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
        INSERT INTO etf_dividend (
            etf_code,
            source_event_id,
            announcement_date,
            ex_dividend_date,
            record_date,
            payment_date,
            amount_per_unit,
            currency,
            source_id,
            import_batch_id,
            source_updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT (
            source_id,
            source_event_id
        )
        DO UPDATE SET
            etf_code =
                excluded.etf_code,
            announcement_date =
                excluded.announcement_date,
            ex_dividend_date =
                excluded.ex_dividend_date,
            record_date =
                excluded.record_date,
            payment_date =
                excluded.payment_date,
            amount_per_unit =
                excluded.amount_per_unit,
            currency =
                excluded.currency,
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
                record.source_event_id,
                (
                    record.announcement_date
                    .isoformat()
                    if record.announcement_date
                    else None
                ),
                (
                    record.ex_dividend_date
                    .isoformat()
                    if record.ex_dividend_date
                    else None
                ),
                (
                    record.record_date
                    .isoformat()
                    if record.record_date
                    else None
                ),
                (
                    record.payment_date
                    .isoformat()
                    if record.payment_date
                    else None
                ),
                float(
                    record.amount_per_unit
                ),
                record.currency,
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

    return DividendUpsertSummary(
        total_records=len(records),
        inserted_records=inserted_records,
        updated_records=updated_records,
    )


def _resolve_dividend_ids(
    connection: sqlite3.Connection,
    records: list[
        ETFDividendComponentImportRecord
    ],
) -> dict[
    tuple[str, str],
    int,
]:
    """Resolve component parent events by ETF and source-event ID."""

    parent_keys = {
        (
            record.etf_code,
            record.dividend_source_event_id,
        )
        for record in records
    }

    resolved: dict[
        tuple[str, str],
        int,
    ] = {}

    for etf_code, source_event_id in sorted(
        parent_keys
    ):
        rows = connection.execute(
            """
            SELECT
                id,
                source_id
            FROM etf_dividend
            WHERE etf_code = ?
              AND source_event_id = ?
            ORDER BY id;
            """,
            (
                etf_code,
                source_event_id,
            ),
        ).fetchall()

        if not rows:
            raise KeyError(
                "找不到配息事件："
                f"{etf_code}/"
                f"{source_event_id}"
            )

        if len(rows) > 1:
            sources = ", ".join(
                row["source_id"]
                for row in rows
            )

            raise ValueError(
                "配息事件識別碼不唯一："
                f"{etf_code}/"
                f"{source_event_id}；"
                f"來源：{sources}"
            )

        resolved[
            (
                etf_code,
                source_event_id,
            )
        ] = int(
            rows[0]["id"]
        )

    return resolved


def _upsert_dividend_component_records(
    connection: sqlite3.Connection,
    records: list[
        ETFDividendComponentImportRecord
    ],
) -> DividendComponentUpsertSummary:
    """Upsert components using an existing transaction."""

    if not records:
        return DividendComponentUpsertSummary(
            total_records=0,
            inserted_records=0,
            updated_records=0,
        )

    parent_ids = _resolve_dividend_ids(
        connection,
        records,
    )

    incoming_rows = [
        (
            parent_ids[
                (
                    record.etf_code,
                    record.dividend_source_event_id,
                )
            ],
            record.component_basis.value,
            record.component_code,
            record.source_id,
            record,
        )
        for record in records
    ]

    existing_rows = connection.execute(
        """
        SELECT
            dividend_id,
            component_basis,
            component_code,
            source_id
        FROM etf_dividend_component;
        """
    ).fetchall()

    existing_keys = {
        (
            int(row["dividend_id"]),
            row["component_basis"],
            row["component_code"],
            row["source_id"],
        )
        for row in existing_rows
    }

    incoming_keys = {
        (
            dividend_id,
            component_basis,
            component_code,
            source_id,
        )
        for (
            dividend_id,
            component_basis,
            component_code,
            source_id,
            _,
        ) in incoming_rows
    }

    inserted_records = len(
        incoming_keys - existing_keys
    )

    updated_records = len(
        incoming_keys & existing_keys
    )

    connection.executemany(
        """
        INSERT INTO etf_dividend_component (
            dividend_id,
            component_code,
            component_basis,
            component_name,
            amount_per_unit,
            ratio_pct,
            source_id,
            import_batch_id,
            source_updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT (
            dividend_id,
            component_basis,
            component_code,
            source_id
        )
        DO UPDATE SET
            component_name =
                excluded.component_name,
            amount_per_unit =
                excluded.amount_per_unit,
            ratio_pct =
                excluded.ratio_pct,
            import_batch_id =
                excluded.import_batch_id,
            source_updated_at =
                excluded.source_updated_at,
            updated_at =
                CURRENT_TIMESTAMP;
        """,
        [
            (
                dividend_id,
                record.component_code,
                component_basis,
                record.component_name,
                (
                    float(
                        record.amount_per_unit
                    )
                    if record.amount_per_unit
                    is not None
                    else None
                ),
                (
                    float(record.ratio_pct)
                    if record.ratio_pct
                    is not None
                    else None
                ),
                source_id,
                record.import_batch_id,
                (
                    record.source_updated_at
                    .isoformat()
                    if record.source_updated_at
                    else None
                ),
            )
            for (
                dividend_id,
                component_basis,
                _,
                source_id,
                record,
            ) in incoming_rows
        ],
    )

    return DividendComponentUpsertSummary(
        total_records=len(records),
        inserted_records=inserted_records,
        updated_records=updated_records,
    )


def upsert_dividend_records(
    records: list[
        ETFDividendImportRecord
    ],
    database_path: str | Path | None = None,
) -> DividendUpsertSummary:
    """Insert or update dividend events."""

    validate_unique_dividend_keys(
        records
    )

    connection = get_connection(
        database_path
    )

    try:
        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        summary = _upsert_dividend_records(
            connection,
            records,
        )

        connection.commit()

        return summary

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def upsert_dividend_component_records(
    records: list[
        ETFDividendComponentImportRecord
    ],
    database_path: str | Path | None = None,
) -> DividendComponentUpsertSummary:
    """Insert or update dividend components."""

    validate_unique_component_keys(
        records
    )

    connection = get_connection(
        database_path
    )

    try:
        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        summary = (
            _upsert_dividend_component_records(
                connection,
                records,
            )
        )

        connection.commit()

        return summary

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def upsert_dividend_dataset(
    dividends: list[
        ETFDividendImportRecord
    ],
    components: list[
        ETFDividendComponentImportRecord
    ],
    database_path: str | Path | None = None,
) -> DividendDatasetUpsertSummary:
    """Atomically upsert dividend events and components."""

    validate_unique_dividend_keys(
        dividends
    )

    validate_unique_component_keys(
        components
    )

    connection = get_connection(
        database_path
    )

    try:
        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        dividend_summary = (
            _upsert_dividend_records(
                connection,
                dividends,
            )
        )

        component_summary = (
            _upsert_dividend_component_records(
                connection,
                components,
            )
        )

        connection.commit()

        return DividendDatasetUpsertSummary(
            dividends=dividend_summary,
            components=component_summary,
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def upsert_dividend_summary_metrics(
    records: list[
        ETFDividendSummaryMetricRecord
    ],
    database_path: str | Path | None = None,
) -> DividendSummaryMetricUpsertSummary:
    """寫入可追溯年季與殖利率，並保留官方優先權。"""

    if not records:
        return DividendSummaryMetricUpsertSummary(
            total_records=0,
            inserted_records=0,
            updated_records=0,
        )

    dividend_ids = [
        record.dividend_id
        for record in records
    ]

    if len(dividend_ids) != len(
        set(dividend_ids)
    ):
        raise ValueError(
            "配息摘要補充資料包含重複 dividend_id"
        )

    connection = get_connection(
        database_path
    )

    try:
        placeholders = ", ".join(
            "?"
            for _ in dividend_ids
        )

        dividend_rows = connection.execute(
            f"""
            SELECT id
            FROM etf_dividend
            WHERE id IN ({placeholders});
            """,
            dividend_ids,
        ).fetchall()

        existing_dividend_ids = {
            int(row["id"])
            for row in dividend_rows
        }

        missing_ids = (
            set(dividend_ids)
            - existing_dividend_ids
        )

        if missing_ids:
            raise KeyError(
                "找不到配息事件："
                + ", ".join(
                    str(value)
                    for value in sorted(
                        missing_ids
                    )
                )
            )

        existing_rows = connection.execute(
            f"""
            SELECT dividend_id
            FROM etf_dividend_summary_metric
            WHERE dividend_id IN ({placeholders});
            """,
            dividend_ids,
        ).fetchall()

        existing_metric_ids = {
            int(row["dividend_id"])
            for row in existing_rows
        }

        connection.execute(
            "BEGIN IMMEDIATE;"
        )

        connection.executemany(
            """
            INSERT INTO etf_dividend_summary_metric (
                dividend_id,
                distribution_period,
                distribution_period_source_id,
                yield_pct,
                yield_basis,
                yield_source_id,
                reference_trade_date,
                reference_close_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (dividend_id)
            DO UPDATE SET
                distribution_period = COALESCE(
                    excluded.distribution_period,
                    etf_dividend_summary_metric
                        .distribution_period
                ),
                distribution_period_source_id = COALESCE(
                    excluded.distribution_period_source_id,
                    etf_dividend_summary_metric
                        .distribution_period_source_id
                ),
                yield_pct = CASE
                    WHEN etf_dividend_summary_metric.yield_basis
                        = 'OFFICIAL'
                        AND excluded.yield_basis = 'CALCULATED'
                    THEN etf_dividend_summary_metric.yield_pct
                    ELSE COALESCE(
                        excluded.yield_pct,
                        etf_dividend_summary_metric.yield_pct
                    )
                END,
                yield_basis = CASE
                    WHEN etf_dividend_summary_metric.yield_basis
                        = 'OFFICIAL'
                        AND excluded.yield_basis = 'CALCULATED'
                    THEN etf_dividend_summary_metric.yield_basis
                    ELSE COALESCE(
                        excluded.yield_basis,
                        etf_dividend_summary_metric.yield_basis
                    )
                END,
                yield_source_id = CASE
                    WHEN etf_dividend_summary_metric.yield_basis
                        = 'OFFICIAL'
                        AND excluded.yield_basis = 'CALCULATED'
                    THEN etf_dividend_summary_metric.yield_source_id
                    ELSE COALESCE(
                        excluded.yield_source_id,
                        etf_dividend_summary_metric.yield_source_id
                    )
                END,
                reference_trade_date = CASE
                    WHEN etf_dividend_summary_metric.yield_basis
                        = 'OFFICIAL'
                        AND excluded.yield_basis = 'CALCULATED'
                    THEN etf_dividend_summary_metric
                        .reference_trade_date
                    WHEN excluded.yield_basis = 'OFFICIAL'
                    THEN NULL
                    ELSE COALESCE(
                        excluded.reference_trade_date,
                        etf_dividend_summary_metric
                            .reference_trade_date
                    )
                END,
                reference_close_price = CASE
                    WHEN etf_dividend_summary_metric.yield_basis
                        = 'OFFICIAL'
                        AND excluded.yield_basis = 'CALCULATED'
                    THEN etf_dividend_summary_metric
                        .reference_close_price
                    WHEN excluded.yield_basis = 'OFFICIAL'
                    THEN NULL
                    ELSE COALESCE(
                        excluded.reference_close_price,
                        etf_dividend_summary_metric
                            .reference_close_price
                    )
                END,
                updated_at = CURRENT_TIMESTAMP;
            """,
            [
                (
                    record.dividend_id,
                    record.distribution_period,
                    (
                        record
                        .distribution_period_source_id
                    ),
                    (
                        float(record.yield_pct)
                        if record.yield_pct
                        is not None
                        else None
                    ),
                    (
                        record.yield_basis.value
                        if record.yield_basis
                        is not None
                        else None
                    ),
                    record.yield_source_id,
                    (
                        record.reference_trade_date
                        .isoformat()
                        if record.reference_trade_date
                        is not None
                        else None
                    ),
                    (
                        float(
                            record
                            .reference_close_price
                        )
                        if record.reference_close_price
                        is not None
                        else None
                    ),
                )
                for record in records
            ],
        )

        connection.commit()

        inserted_records = len(
            set(dividend_ids)
            - existing_metric_ids
        )

        return DividendSummaryMetricUpsertSummary(
            total_records=len(records),
            inserted_records=inserted_records,
            updated_records=(
                len(records)
                - inserted_records
            ),
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def list_dividend_yield_candidates(
    database_path: str | Path | None = None,
    etf_code: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """列出尚無官方或回退殖利率的配息事件。"""

    conditions = [
        "d.ex_dividend_date IS NOT NULL",
        "m.yield_pct IS NULL",
    ]

    parameters: list[Any] = []

    if etf_code is not None:
        conditions.append(
            "d.etf_code = ?"
        )
        parameters.append(
            _normalize_text(
                etf_code,
                "etf_code",
                uppercase=True,
            )
        )

    limit_sql = ""

    if limit is not None:
        if limit < 1:
            raise ValueError(
                "limit 必須大於 0"
            )

        limit_sql = "LIMIT ?"
        parameters.append(limit)

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            SELECT
                d.id AS dividend_id,
                d.etf_code,
                d.ex_dividend_date,
                d.amount_per_unit,
                d.currency
            FROM etf_dividend AS d
            LEFT JOIN etf_dividend_summary_metric AS m
                ON m.dividend_id = d.id
            WHERE {" AND ".join(conditions)}
            ORDER BY
                d.ex_dividend_date DESC,
                d.id DESC
            {limit_sql};
            """,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def get_dividend_id(
    etf_code: str,
    source_event_id: str,
    database_path: str | Path | None = None,
) -> int | None:
    """Return one dividend ID by ETF and event ID."""

    normalized_code = _normalize_text(
        etf_code,
        "etf_code",
        uppercase=True,
    )

    normalized_event_id = _normalize_text(
        source_event_id,
        "source_event_id",
    )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            """
            SELECT id
            FROM etf_dividend
            WHERE etf_code = ?
              AND source_event_id = ?
            ORDER BY id;
            """,
            (
                normalized_code,
                normalized_event_id,
            ),
        ).fetchall()

        if not rows:
            return None

        if len(rows) > 1:
            raise ValueError(
                "配息事件識別碼不唯一："
                f"{normalized_code}/"
                f"{normalized_event_id}"
            )

        return int(
            rows[0]["id"]
        )

    finally:
        connection.close()


def list_etf_dividends(
    etf_code: str,
    database_path: str | Path | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List ETF dividend events, newest first."""

    normalized_code = _normalize_text(
        etf_code,
        "etf_code",
        uppercase=True,
    )

    if limit < 1:
        raise ValueError(
            "limit 必須大於 0"
        )

    if offset < 0:
        raise ValueError(
            "offset 不得小於 0"
        )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            """
            SELECT
                d.id,
                d.etf_code,
                d.source_event_id,
                d.announcement_date,
                d.ex_dividend_date,
                d.record_date,
                d.payment_date,
                d.amount_per_unit,
                d.currency,
                d.source_id,
                d.import_batch_id,
                d.source_updated_at,
                m.distribution_period,
                m.distribution_period_source_id,
                m.yield_pct,
                m.yield_basis,
                m.yield_source_id,
                m.reference_trade_date,
                m.reference_close_price
            FROM etf_dividend AS d
            LEFT JOIN etf_dividend_summary_metric AS m
                ON m.dividend_id = d.id
            WHERE d.etf_code = ?
            ORDER BY
                COALESCE(
                    d.ex_dividend_date,
                    d.record_date,
                    d.payment_date,
                    d.announcement_date
                ) DESC,
                d.id DESC
            LIMIT ?
            OFFSET ?;
            """,
            (
                normalized_code,
                limit,
                offset,
            ),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def list_dividend_components(
    dividend_id: int,
    database_path: str | Path | None = None,
    component_basis: (
        DividendComponentBasis | None
    ) = None,
    source_id: str | None = None,
) -> list[dict[str, Any]]:
    """List components for one dividend event."""

    if dividend_id < 1:
        raise ValueError(
            "dividend_id 必須大於 0"
        )

    conditions = [
        "dividend_id = ?",
    ]

    parameters: list[Any] = [
        dividend_id,
    ]

    if component_basis is not None:
        conditions.append(
            "component_basis = ?"
        )

        parameters.append(
            component_basis.value
        )

    if source_id is not None:
        normalized_source_id = (
            _normalize_text(
                source_id,
                "source_id",
                lowercase=True,
            )
        )

        conditions.append(
            "source_id = ?"
        )

        parameters.append(
            normalized_source_id
        )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            SELECT
                id,
                dividend_id,
                component_code,
                component_basis,
                component_name,
                amount_per_unit,
                ratio_pct,
                source_id,
                import_batch_id,
                source_updated_at
            FROM etf_dividend_component
            WHERE {" AND ".join(conditions)}
            ORDER BY
                CASE component_basis
                    WHEN 'ACTUAL' THEN 0
                    ELSE 1
                END,
                component_code,
                source_id;
            """,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def count_etf_dividends(
    etf_code: str,
    database_path: str | Path | None = None,
) -> int:
    """Count dividend events for one ETF."""

    normalized_code = _normalize_text(
        etf_code,
        "etf_code",
        uppercase=True,
    )

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM etf_dividend
            WHERE etf_code = ?;
            """,
            (normalized_code,),
        ).fetchone()

        return int(
            row["total"]
        )

    finally:
        connection.close()


def get_dividend_by_id(
    dividend_id: int,
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Return one dividend event by database ID."""

    if dividend_id < 1:
        raise ValueError(
            "dividend_id 必須大於 0"
        )

    connection = get_connection(
        database_path
    )

    try:
        row = connection.execute(
            """
            SELECT
                d.id,
                d.etf_code,
                d.source_event_id,
                d.announcement_date,
                d.ex_dividend_date,
                d.record_date,
                d.payment_date,
                d.amount_per_unit,
                d.currency,
                d.source_id,
                d.import_batch_id,
                d.source_updated_at,
                m.distribution_period,
                m.distribution_period_source_id,
                m.yield_pct,
                m.yield_basis,
                m.yield_source_id,
                m.reference_trade_date,
                m.reference_close_price
            FROM etf_dividend AS d
            LEFT JOIN etf_dividend_summary_metric AS m
                ON m.dividend_id = d.id
            WHERE d.id = ?;
            """,
            (dividend_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def list_filtered_dividend_components(
    dividend_id: int,
    database_path: str | Path | None = None,
    component_basis: (
        DividendComponentBasis | None
    ) = None,
    component_code: str | None = None,
    source_id: str | None = None,
) -> list[dict[str, Any]]:
    """List one dividend's components with optional filters."""

    if dividend_id < 1:
        raise ValueError(
            "dividend_id 必須大於 0"
        )

    conditions = [
        "dividend_id = ?",
    ]

    parameters: list[Any] = [
        dividend_id,
    ]

    if component_basis is not None:
        conditions.append(
            "component_basis = ?"
        )

        parameters.append(
            component_basis.value
        )

    if component_code is not None:
        normalized_component_code = (
            _normalize_text(
                component_code,
                "component_code",
                uppercase=True,
            )
        )

        conditions.append(
            "component_code = ?"
        )

        parameters.append(
            normalized_component_code
        )

    if source_id is not None:
        normalized_source_id = (
            _normalize_text(
                source_id,
                "source_id",
                lowercase=True,
            )
        )

        conditions.append(
            "source_id = ?"
        )

        parameters.append(
            normalized_source_id
        )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            f"""
            SELECT
                id,
                dividend_id,
                component_code,
                component_basis,
                component_name,
                amount_per_unit,
                ratio_pct,
                source_id,
                import_batch_id,
                source_updated_at
            FROM etf_dividend_component
            WHERE {" AND ".join(conditions)}
            ORDER BY
                CASE component_basis
                    WHEN 'ACTUAL' THEN 0
                    ELSE 1
                END,
                component_code,
                source_id,
                id;
            """,
            parameters,
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def list_actual_76w_history(
    etf_code: str,
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """List only ACTUAL 76W records for one ETF."""

    normalized_code = _normalize_text(
        etf_code,
        "etf_code",
        uppercase=True,
    )

    connection = get_connection(
        database_path
    )

    try:
        rows = connection.execute(
            """
            SELECT
                d.id AS dividend_id,
                d.source_event_id,
                d.announcement_date,
                d.ex_dividend_date,
                d.record_date,
                d.payment_date,
                d.amount_per_unit,
                d.currency,
                c.amount_per_unit
                    AS component_amount_per_unit,
                c.ratio_pct,
                c.source_id
            FROM etf_dividend_component AS c
            INNER JOIN etf_dividend AS d
                ON d.id = c.dividend_id
            WHERE d.etf_code = ?
              AND c.component_basis = 'ACTUAL'
              AND c.component_code = '76W'
            ORDER BY
                COALESCE(
                    d.ex_dividend_date,
                    d.record_date,
                    d.payment_date,
                    d.announcement_date
                ) DESC,
                d.id DESC,
                c.id DESC;
            """,
            (normalized_code,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def build_actual_76w_summary(
    etf_code: str,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build ACTUAL 76W history statistics for one ETF."""

    normalized_code = _normalize_text(
        etf_code,
        "etf_code",
        uppercase=True,
    )

    total_dividend_count = (
        count_etf_dividends(
            etf_code=normalized_code,
            database_path=database_path,
        )
    )

    items = list_actual_76w_history(
        etf_code=normalized_code,
        database_path=database_path,
    )

    ratio_values = [
        float(item["ratio_pct"])
        for item in items
        if item["ratio_pct"] is not None
    ]

    latest_ratio = (
        float(items[0]["ratio_pct"])
        if (
            items
            and items[0]["ratio_pct"]
            is not None
        )
        else None
    )

    average_ratio = (
        round(
            sum(ratio_values)
            / len(ratio_values),
            6,
        )
        if ratio_values
        else None
    )

    full_76w_count = sum(
        1
        for value in ratio_values
        if value == 100.0
    )

    return {
        "etf_code": normalized_code,
        "total_dividend_count": (
            total_dividend_count
        ),
        "actual_76w_record_count": len(
            items
        ),
        "full_76w_count": (
            full_76w_count
        ),
        "latest_76w_ratio_pct": (
            latest_ratio
        ),
        "average_76w_ratio_pct": (
            average_ratio
        ),
        "items": items,
    }
