"""Prepare the isolated V5-1 detailed-page data candidate."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from backend.app.data_sources.actual_dividend_coverage_pipeline import (
    run_actual_dividend_coverage_pipeline,
)
from backend.app.data_sources.detail_page_coverage import (
    build_detail_page_coverage,
    sha256_file,
    write_coverage_report,
)
from backend.app.data_sources.dividend_pipeline import run_dividend_pipeline
from backend.app.data_sources.dividend_yield_pipeline import (
    run_dividend_yield_pipeline,
)
from backend.app.data_sources.etf_master_pipeline import run_etf_master_pipeline
from backend.app.data_sources.performance_pipeline import (
    run_multi_period_performance_pipeline,
)
from backend.app.database.deployment_readiness import (
    rehearse_database_migration,
)
from backend.app.models.etf_analysis import PerformancePeriod


def prepare_detail_data_candidate(
    source_database: str | Path,
    candidate_database: str | Path,
    artifact_directory: str | Path,
    *,
    evaluated_on: date | None = None,
    request_interval_seconds: float = 0.4,
    inter_etf_interval_seconds: float = 0.5,
) -> dict:
    """Copy, refresh and audit a no-overwrite V5-1 database candidate."""

    source = Path(source_database).resolve()
    candidate = Path(candidate_database).resolve()
    artifacts = Path(artifact_directory).resolve()
    evaluated_on = evaluated_on or date.today()

    if not source.is_file():
        raise FileNotFoundError(f"source database does not exist: {source}")
    if candidate.exists():
        raise FileExistsError(f"candidate database already exists: {candidate}")
    if artifacts.exists():
        raise FileExistsError(f"artifact directory already exists: {artifacts}")
    if source == candidate:
        raise ValueError("source and candidate databases must differ")
    if request_interval_seconds < 0 or inter_etf_interval_seconds < 0:
        raise ValueError("network intervals must not be negative")

    source_sha256 = sha256_file(source)
    migration = rehearse_database_migration(source, candidate)
    artifacts.mkdir(parents=True)

    master = run_etf_master_pipeline(
        database_path=candidate,
        raw_output_root=artifacts / "master" / "raw",
        processed_output_root=artifacts / "master" / "processed",
        rejected_output_root=artifacts / "master" / "rejected",
        report_output_root=artifacts / "master" / "quality",
    )

    performance = run_multi_period_performance_pipeline(
        database_path=candidate,
        end_date=evaluated_on,
        periods=(
            PerformancePeriod.ONE_MONTH,
            PerformancePeriod.THREE_MONTHS,
            PerformancePeriod.SIX_MONTHS,
            PerformancePeriod.ONE_YEAR,
        ),
        candidate_minimum_history_months=0,
        include_bond=True,
        request_interval_seconds=request_interval_seconds,
        inter_etf_interval_seconds=inter_etf_interval_seconds,
        processed_output_root=artifacts / "performance" / "processed",
        rejected_output_root=artifacts / "performance" / "rejected",
        save_raw_snapshots=False,
    )

    dividend = run_dividend_pipeline(
        database_path=candidate,
        raw_output_root=artifacts / "dividend" / "raw",
        processed_output_root=artifacts / "dividend" / "processed",
        rejected_output_root=artifacts / "dividend" / "rejected",
        report_output_root=artifacts / "dividend" / "quality",
        run_at=datetime.now(timezone.utc),
        preserve_event_on_invalid_estimates=True,
    )

    dividend_yield = run_dividend_yield_pipeline(
        database_path=candidate,
        request_interval_seconds=request_interval_seconds,
        today=evaluated_on,
        prefer_cached_prices=True,
    )

    actual = run_actual_dividend_coverage_pipeline(
        database_path=candidate,
        output_root=artifacts / "actual_coverage",
        run_at=datetime.now(timezone.utc),
    )

    coverage_path = artifacts / "detail_page_coverage.report.json"
    coverage = build_detail_page_coverage(candidate)
    write_coverage_report(coverage, coverage_path)

    result = {
        "schema_version": 1,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "evaluated_on": evaluated_on.isoformat(),
        "source_database": {
            "file_name": source.name,
            "sha256": source_sha256,
        },
        "candidate_database": coverage["database"],
        "migration": {
            "schema_ready": migration.readiness.ready,
            "preserved_table_count": len(migration.preserved_tables),
        },
        "master": {
            "raw_record_count": master.raw_record_count,
            "accepted_record_count": master.accepted_record_count,
            "rejected_record_count": master.rejected_record_count,
            "inserted_record_count": master.inserted_record_count,
            "updated_record_count": master.updated_record_count,
        },
        "performance": {
            "candidate_count": performance.candidate_count,
            "successful_count": performance.successful_count,
            "insufficient_history_count": performance.insufficient_history_count,
            "failed_count": performance.failed_count,
            "period_summaries": [
                {
                    **asdict(item),
                    "period_code": item.period_code.value,
                }
                for item in performance.period_summaries
            ],
        },
        "dividend": {
            "raw_record_count": dividend.raw_record_count,
            "accepted_dividend_count": dividend.accepted_dividend_count,
            "accepted_component_count": dividend.accepted_component_count,
            "rejected_record_count": dividend.rejected_record_count,
        },
        "dividend_yield": {
            "candidate_count": dividend_yield.candidate_count,
            "calculated_count": dividend_yield.calculated_count,
            "failed_count": dividend_yield.failed_count,
            "failures": [asdict(item) for item in dividend_yield.failures],
        },
        "actual_coverage": actual.coverage_summary,
        "review_queue_count": actual.review_queue_count,
        "field_coverage": coverage["field_coverage"],
        "coverage_report_path": str(coverage_path),
        "invariants": [
            "No source database was overwritten.",
            "Missing official facts remain UNAVAILABLE.",
            "Estimated capital gain was not relabelled as ACTUAL 76W.",
            "Allocation and Streamlit code were not changed.",
        ],
    }
    manifest_path = artifacts / "candidate_manifest.json"
    manifest_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the isolated V5-1 detail-page data candidate."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--artifacts", required=True, type=Path)
    parser.add_argument("--evaluated-on", type=date.fromisoformat)
    parser.add_argument("--request-interval", type=float, default=0.4)
    parser.add_argument("--between-etf", type=float, default=0.5)
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_network:
        parser.error("candidate refresh requires --allow-network")
    result = prepare_detail_data_candidate(
        args.source,
        args.database,
        args.artifacts,
        evaluated_on=args.evaluated_on,
        request_interval_seconds=args.request_interval,
        inter_etf_interval_seconds=args.between_etf,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    database = result["candidate_database"]
    return 0 if (
        database["integrity_check"] == "ok"
        and database["foreign_key_violation_count"] == 0
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
