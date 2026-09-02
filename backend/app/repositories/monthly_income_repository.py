"""每月領息分布 Repository。"""

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from backend.app.database.connection import (
    get_connection,
)


def calculate_window_start(
    as_of_date: date,
    lookback_years: int,
) -> date:
    """計算含起訖日的滾動年度起點。"""

    try:
        anniversary = as_of_date.replace(
            year=(
                as_of_date.year
                - lookback_years
            ),
        )

    except ValueError:
        anniversary = as_of_date.replace(
            year=(
                as_of_date.year
                - lookback_years
            ),
            day=28,
        )

    return anniversary + timedelta(days=1)


def build_empty_months() -> list[dict[str, Any]]:
    """建立固定 1–12 月的空白月份資料。"""

    return [
        {
            "month": month,
            "event_count": 0,
            "observed_year_count": 0,
            "total_amount_per_unit": None,
            "average_amount_per_event": None,
            "latest_payment_date": None,
        }
        for month in range(1, 13)
    ]


def build_monthly_income_distribution(
    etf_code: str,
    database_path: str | Path | None = None,
    lookback_years: int = 3,
    *,
    analysis_date: date | None = None,
) -> dict[str, Any] | None:
    """依分析日以前的實際入帳日建立單一 ETF 月份分布。"""

    if lookback_years < 1 or lookback_years > 10:
        raise ValueError(
            "lookback_years 必須介於 1 到 10"
        )

    normalized_code = etf_code.strip().upper()

    if not normalized_code:
        return None

    connection = get_connection(
        database_path
    )

    try:
        summary_row = connection.execute(
            """
            SELECT
                e.code,
                e.name,
                COUNT(d.id) AS total_event_count,
                COUNT(d.payment_date) AS dated_event_count,
                MAX(
                    CASE
                        WHEN ? IS NULL
                          OR d.payment_date <= ?
                        THEN d.payment_date
                    END
                ) AS latest_payment_date
            FROM etf_master AS e
            LEFT JOIN etf_dividend AS d
              ON d.etf_code = e.code
            WHERE e.code = ?
            GROUP BY
                e.code,
                e.name;
            """,
            (
                analysis_date.isoformat()
                if analysis_date is not None
                else None,
                analysis_date.isoformat()
                if analysis_date is not None
                else None,
                normalized_code,
            ),
        ).fetchone()

        if summary_row is None:
            return None

        total_event_count = int(
            summary_row["total_event_count"]
        )
        dated_event_count = int(
            summary_row["dated_event_count"]
        )
        latest_payment_text = (
            summary_row["latest_payment_date"]
        )

        if latest_payment_text is None:
            return {
                "etf_code": normalized_code,
                "name": summary_row["name"],
                "date_basis": "PAYMENT_DATE",
                "lookback_years": lookback_years,
                "as_of_date": None,
                "window_start_date": None,
                "total_dividend_event_count": (
                    total_event_count
                ),
                "dated_dividend_event_count": (
                    dated_event_count
                ),
                "missing_payment_date_count": (
                    total_event_count
                    - dated_event_count
                ),
                "analysis_event_count": 0,
                "covered_month_count": 0,
                "covered_month_occurrence_count": 0,
                "analysis_currency": None,
                "has_mixed_currencies": False,
                "total_amount_per_unit": None,
                "months": build_empty_months(),
            }

        as_of_date = date.fromisoformat(
            str(latest_payment_text)
        )
        window_start_date = (
            calculate_window_start(
                as_of_date,
                lookback_years,
            )
        )

        rows = connection.execute(
            """
            SELECT
                payment_date,
                amount_per_unit,
                currency
            FROM etf_dividend
            WHERE etf_code = ?
              AND payment_date >= ?
              AND payment_date <= ?
            ORDER BY payment_date;
            """,
            (
                normalized_code,
                window_start_date.isoformat(),
                as_of_date.isoformat(),
            ),
        ).fetchall()

    finally:
        connection.close()

    currencies = sorted(
        {
            str(row["currency"]).upper()
            for row in rows
        }
    )
    analysis_currency = (
        currencies[0]
        if len(currencies) == 1
        else None
    )
    has_mixed_currencies = (
        len(currencies) > 1
    )
    month_events: dict[
        int,
        list[tuple[date, float]],
    ] = {
        month: []
        for month in range(1, 13)
    }

    for row in rows:
        payment_date = date.fromisoformat(
            str(row["payment_date"])
        )
        month_events[payment_date.month].append(
            (
                payment_date,
                float(row["amount_per_unit"]),
            )
        )

    months: list[dict[str, Any]] = []
    covered_month_occurrences: set[
        tuple[int, int]
    ] = set()

    for month in range(1, 13):
        events = month_events[month]
        observed_years = {
            payment_date.year
            for payment_date, _ in events
        }
        covered_month_occurrences.update(
            (
                payment_date.year,
                payment_date.month,
            )
            for payment_date, _ in events
        )

        amount_total = (
            sum(
                amount
                for _, amount in events
            )
            if events and not has_mixed_currencies
            else None
        )

        months.append(
            {
                "month": month,
                "event_count": len(events),
                "observed_year_count": len(
                    observed_years
                ),
                "total_amount_per_unit": (
                    amount_total
                ),
                "average_amount_per_event": (
                    amount_total / len(events)
                    if amount_total is not None
                    else None
                ),
                "latest_payment_date": (
                    events[-1][0]
                    if events
                    else None
                ),
            }
        )

    return {
        "etf_code": normalized_code,
        "name": summary_row["name"],
        "date_basis": "PAYMENT_DATE",
        "lookback_years": lookback_years,
        "as_of_date": as_of_date,
        "window_start_date": window_start_date,
        "total_dividend_event_count": (
            total_event_count
        ),
        "dated_dividend_event_count": (
            dated_event_count
        ),
        "missing_payment_date_count": (
            total_event_count
            - dated_event_count
        ),
        "analysis_event_count": len(rows),
        "covered_month_count": sum(
            bool(events)
            for events in month_events.values()
        ),
        "covered_month_occurrence_count": len(
            covered_month_occurrences
        ),
        "analysis_currency": analysis_currency,
        "has_mixed_currencies": (
            has_mixed_currencies
        ),
        "total_amount_per_unit": (
            sum(
                float(row["amount_per_unit"])
                for row in rows
            )
            if rows and not has_mixed_currencies
            else None
        ),
        "months": months,
    }
