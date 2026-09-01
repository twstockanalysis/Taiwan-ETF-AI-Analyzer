"""Audit one immutable database against the complete V5 planner matrix."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

from backend.app.data_sources.detail_page_coverage import (
    build_detail_page_coverage,
    sha256_file,
)
from backend.app.models.allocation_results import AllocationResultsRequest
from backend.app.models.public_planner import PublicPlannerHoldingInput
from backend.app.services.allocation_results import build_allocation_results
from backend.app.services.market_eligibility_index import (
    build_market_eligibility_index,
)


def _request(
    target: str,
    months: list[int],
    holdings: list[tuple[str, int]],
) -> AllocationResultsRequest:
    return AllocationResultsRequest(
        target_after_tax_cash_twd=Decimal(target),
        target_months=months,
        existing_holdings=[
            PublicPlannerHoldingInput(etf_code=code, held_units=units)
            for code, units in holdings
        ],
        history_years=3,
        cash_deduction_rate_pct=Decimal("0"),
    )


def _missing_price_code(database: Path) -> str | None:
    connection = sqlite3.connect(database)
    try:
        row = connection.execute(
            """
            SELECT master.code
            FROM etf_master AS master
            LEFT JOIN etf_daily_close AS close
              ON close.etf_code = master.code
            GROUP BY master.code
            HAVING COUNT(close.trade_date) = 0
            ORDER BY master.code
            LIMIT 1;
            """
        ).fetchone()
    finally:
        connection.close()
    return str(row[0]) if row is not None else None


def build_audit_cases(database: Path) -> list[tuple[str, AllocationResultsRequest]]:
    cases = [
        (
            "zero_holdings_quarterly_100",
            _request("100", [1, 4, 7, 10], []),
        ),
        (
            "holding_0050_quarterly_100",
            _request("100", [1, 4, 7, 10], [("0050", 10)]),
        ),
        (
            "holdings_0050_00878_quarterly_100",
            _request(
                "100",
                [1, 4, 7, 10],
                [("0050", 10), ("00878", 10)],
            ),
        ),
        (
            "zero_holdings_all_months_3000",
            _request("3000", list(range(1, 13)), []),
        ),
        (
            "holding_unsupported_product",
            _request("100", [1, 4, 7, 10], [("00632R", 10)]),
        ),
        (
            "formal_zero_target",
            _request("0", [1, 4, 7, 10], []),
        ),
        (
            "holding_00929_all_months_3000",
            _request("3000", list(range(1, 13)), [("00929", 1000)]),
        ),
    ]
    missing_price = _missing_price_code(database)
    if missing_price is not None:
        cases.append(
            (
                "holding_missing_reference_price",
                _request("100", [1, 4, 7, 10], [(missing_price, 10)]),
            )
        )
    return cases


def _summarize_case(
    case_id: str,
    request: AllocationResultsRequest,
    database: Path,
    evaluated_on: date,
) -> dict:
    response = build_allocation_results(
        request,
        database,
        as_of_date=evaluated_on,
    )
    primary = response.plans[0].result
    exclusion_codes = Counter(
        reason.code
        for candidate in response.excluded_candidates
        for reason in candidate.reasons
        if reason.kind.value == "EXCLUDE"
    )
    return {
        "case_id": case_id,
        "request": request.model_dump(mode="json"),
        "snapshot_id": response.snapshot_id,
        "status": primary.status.value,
        "optimality": primary.optimality.value,
        "universe_count": primary.universe_count,
        "eligible_count": primary.eligible_count,
        "plan_count": len(response.plans),
        "plan_strategies": [plan.strategy.value for plan in response.plans],
        "added_etf_count": len(primary.additions),
        "within_v5_max_five_added_etfs": len(primary.additions) <= 5,
        "total_required_additional_capital": str(
            primary.total_required_additional_capital
        ),
        "additions": [
            {
                "etf_code": item.etf_code,
                "additional_shares": item.additional_shares,
                "required_capital": str(item.required_capital),
                "supported_target_months": item.supported_target_months,
            }
            for item in primary.additions
        ],
        "selected_months": [
            {
                "month": item.month,
                "current_after_tax_cash": str(item.current_after_tax_cash),
                "added_after_tax_cash": str(item.added_after_tax_cash),
                "shortfall": str(item.shortfall),
            }
            for item in primary.monthly_results
            if item.month in request.target_months
        ],
        "issue_codes": [item.code for item in primary.issues],
        "strategy_issue_codes": [
            item.code for item in response.strategy_issues
        ],
        "exclusion_codes": [
            {"code": code, "count": count}
            for code, count in sorted(
                exclusion_codes.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ],
    }


def _reference_etf_evidence(
    database: Path,
    evaluated_on: date,
    etf_code: str,
) -> dict:
    request = _request("3000", list(range(1, 13)), [])
    index = build_market_eligibility_index(
        request,
        database,
        as_of_date=evaluated_on,
    ).response
    candidate = next(
        item for item in index.candidates if item.etf_code == etf_code
    )
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT source_event_id, payment_date, amount_per_unit, source_id
            FROM etf_dividend
            WHERE etf_code = ?
            ORDER BY payment_date;
            """,
            (etf_code,),
        ).fetchall()
        master = connection.execute(
            """
            SELECT code, name, is_active, is_bond, listing_date
            FROM etf_master
            WHERE code = ?;
            """,
            (etf_code,),
        ).fetchone()
    finally:
        connection.close()
    paid = [
        dict(row)
        for row in rows
        if row["payment_date"] is not None
        and date.fromisoformat(str(row["payment_date"])) <= evaluated_on
    ]
    future = [
        dict(row)
        for row in rows
        if row["payment_date"] is not None
        and date.fromisoformat(str(row["payment_date"])) > evaluated_on
    ]
    return {
        "etf_code": etf_code,
        "master": dict(master) if master is not None else None,
        "is_active_field_semantics": "ACTIVELY_MANAGED_ETF_NOT_LISTING_STATUS",
        "eligible_for_addition": candidate.eligible_for_addition,
        "reason_codes": [reason.code for reason in candidate.reasons],
        "latest_payment_date_used_by_current_index": (
            candidate.latest_payment_date.isoformat()
            if candidate.latest_payment_date is not None
            else None
        ),
        "paid_event_count_as_of_evaluation": len(paid),
        "future_scheduled_payment_event_count": len(future),
        "latest_paid_event": paid[-1] if paid else None,
        "future_scheduled_events": future,
    }


def build_full_database_audit(
    database_path: str | Path,
    *,
    evaluated_on: date,
) -> dict:
    database = Path(database_path).resolve()
    if not database.is_file():
        raise FileNotFoundError(f"database does not exist: {database}")
    coverage = build_detail_page_coverage(database)
    cases = [
        _summarize_case(case_id, request, database, evaluated_on)
        for case_id, request in build_audit_cases(database)
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluated_on": evaluated_on.isoformat(),
        "database": {
            **coverage["database"],
            "sha256_verified": sha256_file(database),
        },
        "field_coverage": coverage["field_coverage"],
        "planner_cases": cases,
        "reference_etfs": [
            _reference_etf_evidence(database, evaluated_on, "00929")
        ],
        "acceptance": {
            "all_cases_have_explicit_result_state": all(
                bool(case["status"]) for case in cases
            ),
            "all_normal_target_met_cases_within_five_additions": all(
                case["within_v5_max_five_added_etfs"]
                for case in cases
                if case["status"] == "TARGET_MET"
                and Decimal(
                    case["request"]["target_after_tax_cash_twd"]
                ) > 0
            ),
            "existing_holding_cases_have_eligible_candidates": all(
                case["eligible_count"] > 0
                for case in cases
                if case["request"]["existing_holdings"]
            ),
        },
        "invariants": [
            "The audit is read-only and does not mutate the candidate database.",
            "Missing data remains unavailable rather than formal zero.",
            "Future scheduled payments are counted separately from paid history.",
            "The audit changes no allocation objective or public page.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit one immutable database against the full V5 matrix."
    )
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--evaluated-on", required=True, type=date.fromisoformat)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"output already exists: {args.output}")
    result = build_full_database_audit(
        args.database,
        evaluated_on=args.evaluated_on,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
