"""Evaluate the M12-6 reviewed ACTUAL/76W launch-data gate."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.app.config.settings import DATABASE_PATH
from backend.app.repositories.dividend_quality_repository import (
    build_actual_dividend_coverage_summary,
)


@dataclass(frozen=True, slots=True)
class LaunchDataThreshold:
    """Minimum reviewed records required for an ordinary launch."""

    actual_component_event_count: int = 1
    actual_76w_event_count: int = 1
    source_document_event_count: int = 1


def evaluate_launch_data(
    summary: dict,
    *,
    threshold: LaunchDataThreshold | None = None,
    limited_coverage_approved_by: str | None = None,
    limited_coverage_reason: str | None = None,
    evaluated_at: datetime | None = None,
) -> dict:
    """Return a machine-readable READY, LIMITED_APPROVED or NO_GO decision."""

    threshold = threshold or LaunchDataThreshold()
    evaluated_at = evaluated_at or datetime.now(timezone.utc)

    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")

    approved_by = (limited_coverage_approved_by or "").strip()
    approval_reason = (limited_coverage_reason or "").strip()

    if bool(approved_by) != bool(approval_reason):
        raise ValueError(
            "limited coverage approval requires both approved-by and reason"
        )

    checks = [
        {
            "name": "dividend_events_present",
            "actual": summary["total_dividend_count"],
            "minimum": 1,
            "passed": summary["total_dividend_count"] >= 1,
        },
        {
            "name": "reviewed_actual_components",
            "actual": summary["actual_component_event_count"],
            "minimum": threshold.actual_component_event_count,
            "passed": summary["actual_component_event_count"]
            >= threshold.actual_component_event_count,
        },
        {
            "name": "reviewed_actual_76w",
            "actual": summary["actual_76w_event_count"],
            "minimum": threshold.actual_76w_event_count,
            "passed": summary["actual_76w_event_count"]
            >= threshold.actual_76w_event_count,
        },
        {
            "name": "traceable_source_documents",
            "actual": summary["source_document_event_count"],
            "minimum": threshold.source_document_event_count,
            "passed": summary["source_document_event_count"]
            >= threshold.source_document_event_count,
        },
    ]

    gate_passed = all(check["passed"] for check in checks)
    limited_approval = bool(approved_by and approval_reason)

    if gate_passed:
        decision = "READY"
        exit_code = 0
    elif limited_approval:
        decision = "LIMITED_APPROVED"
        exit_code = 0
    else:
        decision = "NO_GO"
        exit_code = 1

    return {
        "schema_version": 1,
        "evaluated_at": evaluated_at.isoformat(),
        "decision": decision,
        "exit_code": exit_code,
        "threshold": asdict(threshold),
        "coverage": summary,
        "checks": checks,
        "limited_coverage_approval": (
            {
                "approved_by": approved_by,
                "reason": approval_reason,
            }
            if limited_approval
            else None
        ),
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate the M12-6 reviewed ACTUAL/76W launch-data gate."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DATABASE_PATH,
        help="Existing SQLite database to evaluate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON decision output path.",
    )
    parser.add_argument("--limited-approved-by")
    parser.add_argument("--limited-reason")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)

    if not args.database.is_file():
        raise FileNotFoundError(f"database does not exist: {args.database}")

    summary = build_actual_dividend_coverage_summary(args.database)
    result = evaluate_launch_data(
        summary,
        limited_coverage_approved_by=args.limited_approved_by,
        limited_coverage_reason=args.limited_reason,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")

    print(payload)
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
