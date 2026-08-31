"""Replay the frozen V5 planner requests against one immutable database."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from backend.app.data_sources.detail_page_coverage import sha256_file
from backend.app.models.allocation_results import AllocationResultsRequest
from backend.app.models.public_planner import PublicPlannerHoldingInput
from backend.app.services.allocation_results import build_allocation_results


def _request(holdings: list[tuple[str, int]]) -> AllocationResultsRequest:
    return AllocationResultsRequest(
        target_after_tax_cash_twd=Decimal("100"),
        target_months=[1, 4, 7, 10],
        existing_holdings=[
            PublicPlannerHoldingInput(etf_code=code, held_units=units)
            for code, units in holdings
        ],
        history_years=3,
        cash_deduction_rate_pct=Decimal("0"),
    )


FROZEN_CASES = (
    ("zero_holdings", _request([])),
    ("holding_0050", _request([("0050", 10)])),
    ("holdings_0050_00878", _request([("0050", 10), ("00878", 10)])),
    ("holding_0051", _request([("0051", 10)])),
)


def replay_frozen_planner_cases(
    database_path: str | Path,
    *,
    evaluated_on: date,
) -> dict:
    database = Path(database_path).resolve()
    if not database.is_file():
        raise FileNotFoundError(f"database does not exist: {database}")

    cases = []
    for case_id, request in FROZEN_CASES:
        response = build_allocation_results(
            request,
            database,
            as_of_date=evaluated_on,
        )
        primary = response.plans[0].result
        exclusion_codes = Counter(
            reason.code
            for item in response.excluded_candidates
            for reason in item.reasons
            if reason.kind.value == "EXCLUDE"
        )
        cases.append(
            {
                "case_id": case_id,
                "request": request.model_dump(mode="json"),
                "snapshot_id": response.snapshot_id,
                "status": primary.status.value,
                "optimality": primary.optimality.value,
                "universe_count": primary.universe_count,
                "eligible_count": primary.eligible_count,
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
                "top_exclusion_codes": [
                    {"code": code, "count": count}
                    for code, count in exclusion_codes.most_common(10)
                ],
                "plan_strategies": [item.strategy.value for item in response.plans],
                "strategy_issue_codes": [
                    item.code for item in response.strategy_issues
                ],
            }
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluated_on": evaluated_on.isoformat(),
        "database": {
            "file_name": database.name,
            "sha256": sha256_file(database),
        },
        "cases": cases,
        "notes": [
            "The same four frozen requests are used before and after enrichment.",
            "Results are deterministic historical scenarios, not buy or sell instructions.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay frozen V5 planner cases.")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--evaluated-on", required=True, type=date.fromisoformat)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(f"output already exists: {args.output}")
    result = replay_frozen_planner_cases(
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
