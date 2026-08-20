"""Prepare and verify an isolated database for owner calculation testing."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from backend.app.data_sources.constituent_batch_pipeline import (
    build_constituent_batch_plan,
    run_constituent_batch_pipeline,
)
from backend.app.data_sources.dividend_pipeline import run_dividend_pipeline
from backend.app.data_sources.performance_pipeline import (
    run_multi_period_performance_pipeline,
)
from backend.app.database.deployment_readiness import (
    rehearse_database_migration,
    verify_database_schema,
)
from backend.app.models.etf_analysis import PerformancePeriod
from backend.app.repositories.daily_close_repository import (
    get_latest_daily_close,
)
from backend.app.repositories.dividend_repository import (
    list_etf_component_history,
)
from backend.app.repositories.etf_repository import get_etf_by_code
from backend.app.repositories.monthly_income_repository import (
    build_monthly_income_distribution,
)
from backend.app.repositories.performance_repository import (
    list_latest_etf_performance,
)
from backend.app.services.constituent_data_quality import (
    ConstituentQualityThreshold,
    evaluate_constituent_data_quality,
)
from backend.app.services.target_analysis_data import (
    is_dividend_data_stale,
    is_performance_data_stale,
)
from backend.app.services.tax_reinvestment_data import (
    select_calculation_component_mix,
)


_REQUIRED_PERIODS = ("1M", "3M", "6M", "1Y")


def _date(value) -> date | None:
    if isinstance(value, date):
        return value
    if value:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None
    return None


def _normalize_codes(codes: list[str] | tuple[str, ...] | None) -> list[str]:
    return sorted(
        {
            code.strip().upper()
            for code in (codes or ())
            if code.strip()
        }
    )


def _target_codes(
    database_path: str | Path,
    requested_codes: list[str] | tuple[str, ...] | None,
) -> tuple[list[str], dict[str, str]]:
    plan = build_constituent_batch_plan(database_path)
    status_by_code = {item.etf_code: item.status for item in plan}
    normalized = _normalize_codes(requested_codes)
    if normalized:
        missing = sorted(set(normalized) - set(status_by_code))
        if missing:
            raise ValueError(f"ETF master does not contain: {', '.join(missing)}")
        return normalized, status_by_code
    return (
        sorted(
            item.etf_code
            for item in plan
            if item.status != "NOT_EQUITY"
        ),
        status_by_code,
    )


def _evaluate_one(
    etf_code: str,
    database_path: str | Path,
    *,
    evaluated_on: date,
    history_years: int,
    plan_status: str,
) -> dict:
    core_reasons: list[str] = []
    overlap_reasons: list[str] = []
    etf = get_etf_by_code(etf_code, database_path)
    if etf is None:
        raise ValueError(f"ETF master does not contain: {etf_code}")
    if plan_status == "NOT_EQUITY":
        overlap_reasons.append("NOT_EQUITY_OVERLAP_SCOPE")
    elif plan_status == "UNMAPPED_ISSUER":
        overlap_reasons.append("UNMAPPED_CONSTITUENT_ISSUER")

    performance_rows = list_latest_etf_performance(etf_code, database_path)
    performance_by_period = {
        str(row["period_code"]): row
        for row in performance_rows
        if row.get("metric_code") == "PRICE_RETURN"
    }
    performance_dates: dict[str, str | None] = {}
    for period in _REQUIRED_PERIODS:
        row = performance_by_period.get(period)
        parsed = _date(row.get("as_of_date")) if row else None
        performance_dates[period] = parsed.isoformat() if parsed else None
        if parsed is None:
            core_reasons.append(f"MISSING_PERFORMANCE_{period}")
        elif parsed > evaluated_on:
            core_reasons.append(f"FUTURE_PERFORMANCE_{period}")
        elif is_performance_data_stale(parsed, evaluated_on):
            core_reasons.append(f"STALE_PERFORMANCE_{period}")

    close = get_latest_daily_close(etf_code, database_path)
    close_date = _date(close.get("trade_date")) if close else None
    if close_date is None:
        core_reasons.append("MISSING_DAILY_CLOSE")
    elif close_date > evaluated_on:
        core_reasons.append("FUTURE_DAILY_CLOSE")
    elif is_performance_data_stale(close_date, evaluated_on):
        core_reasons.append("STALE_DAILY_CLOSE")

    monthly = build_monthly_income_distribution(
        etf_code,
        database_path,
        history_years,
    )
    latest_payment = _date(monthly.get("as_of_date")) if monthly else None
    if monthly is None or not monthly.get("analysis_event_count"):
        core_reasons.append("MISSING_DIVIDEND_HISTORY")
    elif monthly.get("has_mixed_currencies"):
        core_reasons.append("MIXED_DIVIDEND_CURRENCIES")
    elif latest_payment and is_dividend_data_stale(
        latest_payment,
        evaluated_on,
    ):
        core_reasons.append("STALE_DIVIDEND_HISTORY")

    component_selection = select_calculation_component_mix(
        list_etf_component_history(etf_code, database_path)
    )
    if component_selection is None:
        core_reasons.append("MISSING_COMPLETE_DIVIDEND_COMPONENTS")

    constituent_quality = evaluate_constituent_data_quality(
        [{"etf_code": etf_code, "issuer_key": etf_code}],
        database_path,
        evaluated_on=evaluated_on,
        threshold=ConstituentQualityThreshold(
            minimum_etf_coverage_pct=Decimal("100"),
            minimum_issuer_coverage_pct=Decimal("100"),
        ),
    )
    if constituent_quality["decision"] != "READY":
        overlap_reasons.extend(
            f"CONSTITUENT_{reason}"
            for item in constituent_quality["items"]
            for reason in item["reasons"]
        )

    constituent_item = constituent_quality["items"][0]
    normalized_core_reasons = sorted(set(core_reasons))
    normalized_overlap_reasons = sorted(set(overlap_reasons))
    return {
        "etf_code": etf_code,
        "name": etf["name"],
        "core_ready": not normalized_core_reasons,
        "overlap_ready": not normalized_overlap_reasons,
        "ready": not normalized_core_reasons and not normalized_overlap_reasons,
        "core_reasons": normalized_core_reasons,
        "overlap_reasons": normalized_overlap_reasons,
        "reasons": sorted(
            set(normalized_core_reasons + normalized_overlap_reasons)
        ),
        "performance_as_of": performance_dates,
        "daily_close_as_of": close_date.isoformat() if close_date else None,
        "latest_payment_date": (
            latest_payment.isoformat() if latest_payment else None
        ),
        "dividend_event_count": (
            int(monthly.get("analysis_event_count", 0)) if monthly else 0
        ),
        "component_basis": (
            component_selection.basis if component_selection else None
        ),
        "constituent_as_of": constituent_item["as_of_date"],
        "constituent_disclosed_weight_pct": constituent_item[
            "disclosed_weight_pct"
        ],
    }


def evaluate_calculation_candidate(
    database_path: str | Path,
    *,
    etf_codes: list[str] | tuple[str, ...] | None = None,
    evaluated_on: date | None = None,
    history_years: int = 3,
) -> dict:
    """Return a strict per-ETF calculation readiness decision."""

    if history_years < 1 or history_years > 10:
        raise ValueError("history_years must be between 1 and 10")
    evaluated_on = evaluated_on or date.today()
    readiness = verify_database_schema(database_path)
    if not readiness.ready:
        return {
            "schema_version": 1,
            "evaluated_on": evaluated_on.isoformat(),
            "database": Path(database_path).name,
            "decision": "NO_GO",
            "exit_code": 1,
            "schema_ready": False,
            "target_etf_count": 0,
            "ready_etf_count": 0,
            "core_ready_etf_count": 0,
            "overlap_ready_etf_count": 0,
            "ready_etf_coverage_pct": "0",
            "items": [],
        }

    targets, status_by_code = _target_codes(database_path, etf_codes)
    items = [
        _evaluate_one(
            code,
            database_path,
            evaluated_on=evaluated_on,
            history_years=history_years,
            plan_status=status_by_code[code],
        )
        for code in targets
    ]
    ready_count = sum(item["ready"] for item in items)
    core_ready_count = sum(item["core_ready"] for item in items)
    overlap_ready_count = sum(item["overlap_ready"] for item in items)
    coverage = (
        Decimal(ready_count) * Decimal("100") / Decimal(len(items))
        if items
        else Decimal("0")
    ).quantize(Decimal("0.000001"))
    ready = bool(items) and ready_count == len(items)
    core_ready = bool(items) and core_ready_count == len(items)
    decision = "READY" if ready else "CORE_READY" if core_ready else "NO_GO"
    return {
        "schema_version": 1,
        "evaluated_on": evaluated_on.isoformat(),
        "database": Path(database_path).name,
        "decision": decision,
        "exit_code": 0 if core_ready else 1,
        "schema_ready": True,
        "history_years": history_years,
        "target_etf_count": len(items),
        "ready_etf_count": ready_count,
        "core_ready_etf_count": core_ready_count,
        "overlap_ready_etf_count": overlap_ready_count,
        "ready_etf_coverage_pct": str(coverage),
        "items": items,
    }


def prepare_calculation_candidate(
    source_database: str | Path,
    candidate_database: str | Path,
    artifact_directory: str | Path,
    *,
    etf_codes: list[str] | tuple[str, ...] | None = None,
    evaluated_on: date | None = None,
    history_years: int = 3,
    request_interval_seconds: float = 0.4,
    inter_etf_interval_seconds: float = 0.5,
) -> dict:
    """Copy, migrate, refresh, and verify a no-overwrite candidate database."""

    evaluated_on = evaluated_on or date.today()
    source = Path(source_database).resolve()
    candidate = Path(candidate_database).resolve()
    artifacts = Path(artifact_directory).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"source database does not exist: {source}")
    if candidate.exists():
        raise FileExistsError(f"candidate database already exists: {candidate}")
    if artifacts.exists():
        raise FileExistsError(f"artifact directory already exists: {artifacts}")
    if source == candidate:
        raise ValueError("source and candidate databases must differ")

    migration = rehearse_database_migration(source, candidate)
    normalized_codes = _normalize_codes(etf_codes)
    performance = run_multi_period_performance_pipeline(
        database_path=candidate,
        end_date=evaluated_on,
        codes=normalized_codes or None,
        periods=[
            PerformancePeriod.ONE_MONTH,
            PerformancePeriod.THREE_MONTHS,
            PerformancePeriod.SIX_MONTHS,
            PerformancePeriod.ONE_YEAR,
        ],
        candidate_minimum_history_months=0,
        request_interval_seconds=request_interval_seconds,
        inter_etf_interval_seconds=inter_etf_interval_seconds,
        processed_output_root=artifacts / "performance" / "processed",
        rejected_output_root=artifacts / "performance" / "rejected",
        save_raw_snapshots=False,
    )

    dividend_results = []
    if normalized_codes:
        start_year = evaluated_on.year - history_years
        for index, code in enumerate(normalized_codes):
            result = run_dividend_pipeline(
                database_path=candidate,
                raw_output_root=artifacts / "dividend" / code / "raw",
                processed_output_root=(
                    artifacts / "dividend" / code / "processed"
                ),
                rejected_output_root=(
                    artifacts / "dividend" / code / "rejected"
                ),
                report_output_root=(
                    artifacts / "dividend" / code / "reports"
                ),
                run_at=datetime.now(timezone.utc) + timedelta(seconds=index),
                etf_code=code,
                start_year=start_year,
                end_year=evaluated_on.year,
                preserve_event_on_invalid_estimates=True,
            )
            dividend_results.append(
                {
                    "etf_code": code,
                    "accepted_dividend_count": result.accepted_dividend_count,
                    "accepted_component_count": result.accepted_component_count,
                    "rejected_record_count": result.rejected_record_count,
                }
            )
    else:
        result = run_dividend_pipeline(
            database_path=candidate,
            raw_output_root=artifacts / "dividend" / "raw",
            processed_output_root=artifacts / "dividend" / "processed",
            rejected_output_root=artifacts / "dividend" / "rejected",
            report_output_root=artifacts / "dividend" / "reports",
            preserve_event_on_invalid_estimates=True,
        )
        dividend_results.append(
            {
                "etf_code": None,
                "accepted_dividend_count": result.accepted_dividend_count,
                "accepted_component_count": result.accepted_component_count,
                "rejected_record_count": result.rejected_record_count,
            }
        )

    constituents = run_constituent_batch_pipeline(
        candidate,
        etf_codes=set(normalized_codes) if normalized_codes else None,
        evaluated_on=evaluated_on,
    )
    decision = evaluate_calculation_candidate(
        candidate,
        etf_codes=normalized_codes or None,
        evaluated_on=evaluated_on,
        history_years=history_years,
    )
    return {
        "schema_version": 1,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "source_database": source.name,
        "candidate_database": candidate.name,
        "schema_ready": migration.readiness.ready,
        "preserved_table_count": len(migration.preserved_tables),
        "performance": {
            "candidate_count": performance.candidate_count,
            "successful_count": performance.successful_count,
            "insufficient_history_count": performance.insufficient_history_count,
            "failed_count": performance.failed_count,
            "period_summaries": [
                {
                    **asdict(summary),
                    "period_code": summary.period_code.value,
                }
                for summary in performance.period_summaries
            ],
        },
        "dividend": dividend_results,
        "constituent": {
            "eligible_automated_count": constituents[
                "eligible_automated_count"
            ],
            "imported_count": constituents["imported_count"],
            "unchanged_count": constituents["unchanged_count"],
            "failed_count": constituents["failed_count"],
            "decision": constituents["quality"]["decision"],
            "failed_items": [
                item
                for item in constituents["results"]
                if item["outcome"] == "FAILED"
            ],
        },
        "calculation_data": decision,
    }


def _write_result(result: dict, output: Path | None) -> None:
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if output is not None:
        if output.exists():
            raise FileExistsError(f"output report already exists: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare or verify isolated ETF calculation data."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check")
    check.add_argument("--database", required=True, type=Path)
    check.add_argument("--etf-code", action="append", dest="etf_codes")
    check.add_argument("--history-years", type=int, default=3)
    check.add_argument("--evaluated-on", type=date.fromisoformat)
    check.add_argument("--output", type=Path)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--source", required=True, type=Path)
    prepare.add_argument("--database", required=True, type=Path)
    prepare.add_argument("--artifacts", required=True, type=Path)
    prepare.add_argument("--etf-code", action="append", dest="etf_codes")
    prepare.add_argument("--history-years", type=int, default=3)
    prepare.add_argument("--evaluated-on", type=date.fromisoformat)
    prepare.add_argument("--request-interval", type=float, default=0.4)
    prepare.add_argument("--between-etf", type=float, default=0.5)
    prepare.add_argument("--allow-network", action="store_true")
    prepare.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        raise FileExistsError(f"output report already exists: {args.output}")
    if args.command == "check":
        result = evaluate_calculation_candidate(
            args.database,
            etf_codes=args.etf_codes,
            evaluated_on=args.evaluated_on,
            history_years=args.history_years,
        )
    else:
        if not args.allow_network:
            parser.error("candidate refresh requires --allow-network")
        result = prepare_calculation_candidate(
            args.source,
            args.database,
            args.artifacts,
            etf_codes=args.etf_codes,
            evaluated_on=args.evaluated_on,
            history_years=args.history_years,
            request_interval_seconds=args.request_interval,
            inter_etf_interval_seconds=args.between_etf,
        )
    _write_result(result, args.output)
    decision = result.get("calculation_data", result)
    return int(decision["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
