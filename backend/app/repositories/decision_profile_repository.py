"""M11-1 單一使用者條件與手動持有部位 Repository。"""

from decimal import Decimal
from pathlib import Path
from typing import Any

from backend.app.database.connection import get_connection
from backend.app.models.decision_profile import (
    ManualHoldingUpsert,
    UserConditionsUpsert,
)


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def get_user_conditions(
    database_path: str | Path | None = None,
) -> dict[str, Any] | None:
    connection = get_connection(database_path)
    try:
        row = connection.execute(
            """
            SELECT
                monthly_after_tax_target,
                analysis_years,
                history_years,
                cash_deduction_rate_pct,
                currency,
                updated_at
            FROM decision_profile
            WHERE id = 1;
            """
        ).fetchone()
        if row is None:
            return None
        return {
            **dict(row),
            "monthly_after_tax_target": _decimal(
                row["monthly_after_tax_target"]
            ),
            "cash_deduction_rate_pct": _decimal(
                row["cash_deduction_rate_pct"]
            ),
        }
    finally:
        connection.close()


def upsert_user_conditions(
    value: UserConditionsUpsert,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    connection = get_connection(database_path)
    try:
        connection.execute(
            """
            INSERT INTO decision_profile (
                id,
                monthly_after_tax_target,
                analysis_years,
                history_years,
                cash_deduction_rate_pct,
                currency
            )
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                monthly_after_tax_target = excluded.monthly_after_tax_target,
                analysis_years = excluded.analysis_years,
                history_years = excluded.history_years,
                cash_deduction_rate_pct = excluded.cash_deduction_rate_pct,
                currency = excluded.currency,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (
                str(value.monthly_after_tax_target),
                value.analysis_years,
                value.history_years,
                (
                    str(value.cash_deduction_rate_pct)
                    if value.cash_deduction_rate_pct is not None
                    else None
                ),
                value.currency,
            ),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    result = get_user_conditions(database_path)
    if result is None:
        raise RuntimeError("使用者條件寫入後未能讀回")
    return result


def list_manual_holdings(
    database_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    connection = get_connection(database_path)
    try:
        rows = connection.execute(
            """
            SELECT
                h.etf_code,
                e.name,
                e.is_active,
                e.is_bond,
                h.held_units,
                h.unit_price,
                h.price_as_of_date,
                h.currency,
                h.updated_at
            FROM manual_holding AS h
            JOIN etf_master AS e
              ON e.code = h.etf_code
            ORDER BY h.etf_code;
            """
        ).fetchall()
        return [
            {
                **dict(row),
                "is_active": bool(row["is_active"]),
                "is_bond": bool(row["is_bond"]),
                "unit_price": _decimal(row["unit_price"]),
            }
            for row in rows
        ]
    finally:
        connection.close()


def upsert_manual_holding(
    etf_code: str,
    value: ManualHoldingUpsert,
    database_path: str | Path | None = None,
) -> dict[str, Any]:
    normalized_code = etf_code.strip().upper()
    connection = get_connection(database_path)
    try:
        connection.execute(
            """
            INSERT INTO manual_holding (
                etf_code,
                held_units,
                unit_price,
                price_as_of_date,
                currency
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(etf_code) DO UPDATE SET
                held_units = excluded.held_units,
                unit_price = excluded.unit_price,
                price_as_of_date = excluded.price_as_of_date,
                currency = excluded.currency,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (
                normalized_code,
                value.held_units,
                str(value.unit_price),
                (
                    value.price_as_of_date.isoformat()
                    if value.price_as_of_date is not None
                    else None
                ),
                value.currency,
            ),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return next(
        item
        for item in list_manual_holdings(database_path)
        if item["etf_code"] == normalized_code
    )


def delete_manual_holding(
    etf_code: str,
    database_path: str | Path | None = None,
) -> bool:
    connection = get_connection(database_path)
    try:
        cursor = connection.execute(
            "DELETE FROM manual_holding WHERE etf_code = ?;",
            (etf_code.strip().upper(),),
        )
        connection.commit()
        return cursor.rowcount > 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
