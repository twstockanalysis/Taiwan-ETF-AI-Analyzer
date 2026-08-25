"""全市場官方 ETF 成分股批次匯入與品質報告。"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable

from backend.app.config.settings import DATABASE_PATH
from backend.app.data_sources.constituent_pipeline import (
    OfficialConstituentImportResult,
    import_official_constituents_with_status,
)
from backend.app.data_sources.constituent_source_registry import (
    CONSTITUENT_SOURCES,
    ConstituentSourceStatus,
)
from backend.app.database.init_db import initialize_database
from backend.app.database.connection import get_connection
from backend.app.repositories.etf_repository import list_etfs
from backend.app.services.constituent_data_quality import (
    ConstituentQualityThreshold,
    evaluate_constituent_data_quality,
)
from backend.app.services.etf_product_scope import (
    unsupported_allocation_product_reason,
)


ISSUER_NAME_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("alliancebernstein", ("聯博",)),
    ("jpmorgan", ("摩根",)),
    ("blackrock", ("貝萊德",)),
    ("franklin", ("富蘭克林", "FT")),
    ("hnh", ("華南永昌",)),
    ("sinopac", ("永豐",)),
    ("yuanta", ("元大",)),
    ("fubon", ("富邦", "FB")),
    ("cathay", ("國泰",)),
    ("first", ("第一金",)),
    ("fuh_hwa", ("復華", "FH")),
    ("capital", ("群益",)),
    ("taishin", ("台新",)),
    ("ctbc", ("中信",)),
    ("upam", ("統一",)),
    ("jko", ("街口",)),
    ("mega", ("兆豐",)),
    ("kgi", ("凱基",)),
    ("uob", ("大華",)),
    ("nomura", ("野村",)),
    ("esun", ("玉山",)),
    ("union", ("聯邦",)),
    ("allianz", ("安聯",)),
)

ETF_ISSUER_OVERRIDES: dict[str, str] = {
    # TWSE short name omits the brand; the official full fund name is Fubon.
    "00733": "fubon",
}


@dataclass(frozen=True, slots=True)
class ConstituentBatchPlanItem:
    etf_code: str
    etf_name: str
    issuer_key: str | None
    status: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ConstituentBatchItemResult:
    etf_code: str
    issuer_key: str
    outcome: str
    as_of_date: str | None = None
    disclosed_weight_pct: str | None = None
    constituent_count: int | None = None
    error: str | None = None


def resolve_constituent_issuer(
    etf_name: str,
    etf_code: str | None = None,
) -> str | None:
    normalized_code = (etf_code or "").strip().upper()
    if normalized_code in ETF_ISSUER_OVERRIDES:
        return ETF_ISSUER_OVERRIDES[normalized_code]
    normalized = etf_name.strip().upper()
    matches = [
        issuer_key
        for issuer_key, markers in ISSUER_NAME_MARKERS
        if any(marker.upper() in normalized for marker in markers)
    ]
    return matches[0] if len(set(matches)) == 1 else None


def build_constituent_batch_plan(
    database_path: str | Path,
) -> list[ConstituentBatchPlanItem]:
    plan: list[ConstituentBatchPlanItem] = []
    connection = get_connection(database_path)
    try:
        performance_codes = {
            row["etf_code"]
            for row in connection.execute(
                """
                SELECT DISTINCT etf_code
                FROM etf_performance
                WHERE metric_code = 'PRICE_RETURN' AND period_code = '6M';
                """
            ).fetchall()
        }
    finally:
        connection.close()
    for etf in list_etfs(database_path, limit=10000):
        code = str(etf["code"])
        name = str(etf["name"])
        reason = unsupported_allocation_product_reason(
            code,
            name,
            bool(etf["is_bond"]),
        )
        issuer_key = resolve_constituent_issuer(name, code)
        if reason is not None:
            status = "NOT_EQUITY"
        elif code not in performance_codes:
            status = "MISSING_PERFORMANCE_BASELINE"
            reason = "NO_6M_PRICE_RETURN"
        elif issuer_key is None:
            status = "UNMAPPED_ISSUER"
            reason = "ETF_NAME_DID_NOT_RESOLVE_TO_REVIEWED_ISSUER"
        else:
            source = CONSTITUENT_SOURCES[issuer_key]
            if source.status == ConstituentSourceStatus.AUTOMATED:
                status = "ELIGIBLE_AUTOMATED"
            else:
                status = "SOURCE_NOT_AUTOMATED"
                reason = source.status.value
        plan.append(ConstituentBatchPlanItem(code, name, issuer_key, status, reason))
    return plan


def run_constituent_batch_pipeline(
    database_path: str | Path,
    *,
    etf_codes: set[str] | None = None,
    evaluated_on: date | None = None,
    threshold: ConstituentQualityThreshold | None = None,
    importer: Callable[[str, str, str | Path], OfficialConstituentImportResult]
    = import_official_constituents_with_status,
) -> dict:
    target_path = initialize_database(database_path)
    plan = build_constituent_batch_plan(target_path)
    if etf_codes:
        normalized_codes = {code.strip().upper() for code in etf_codes}
        plan = [item for item in plan if item.etf_code in normalized_codes]
        found_codes = {item.etf_code for item in plan}
        missing_codes = sorted(normalized_codes - found_codes)
        if missing_codes:
            raise ValueError(f"ETF 主檔找不到：{', '.join(missing_codes)}")

    results: list[ConstituentBatchItemResult] = []
    eligible = [item for item in plan if item.status == "ELIGIBLE_AUTOMATED"]
    for item in eligible:
        try:
            imported = importer(item.issuer_key or "", item.etf_code, target_path)
            snapshot = imported.snapshot
            results.append(
                ConstituentBatchItemResult(
                    item.etf_code,
                    item.issuer_key or "",
                    imported.outcome,
                    snapshot.as_of_date.isoformat(),
                    str(snapshot.total_weight_pct),
                    snapshot.constituent_count,
                )
            )
        except Exception as error:
            results.append(
                ConstituentBatchItemResult(
                    item.etf_code,
                    item.issuer_key or "",
                    "FAILED",
                    error=f"{type(error).__name__}: {error}",
                )
            )

    quality_targets = [
        {"etf_code": item.etf_code, "issuer_key": item.issuer_key}
        for item in plan
        if item.status in {"ELIGIBLE_AUTOMATED", "SOURCE_NOT_AUTOMATED"}
        and item.issuer_key is not None
    ]
    quality = evaluate_constituent_data_quality(
        quality_targets,
        target_path,
        evaluated_on=evaluated_on,
        threshold=threshold,
    )
    unresolved = [
        asdict(item)
        for item in plan
        if item.status in {"UNMAPPED_ISSUER", "SOURCE_NOT_AUTOMATED"}
    ]
    unmapped_count = sum(item.status == "UNMAPPED_ISSUER" for item in plan)
    mapping_check = {
        "name": "eligible_etf_issuer_mapping",
        "actual_unmapped": unmapped_count,
        "maximum_unmapped": 0,
        "passed": unmapped_count == 0,
    }
    quality["checks"].append(mapping_check)
    if not mapping_check["passed"]:
        quality["decision"] = "NO_GO"
    return {
        "schema_version": 1,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "database": Path(target_path).name,
        "plan_count": len(plan),
        "eligible_automated_count": len(eligible),
        "imported_count": sum(item.outcome == "IMPORTED" for item in results),
        "unchanged_count": sum(item.outcome == "UNCHANGED" for item in results),
        "failed_count": sum(item.outcome == "FAILED" for item in results),
        "unresolved_count": len(unresolved),
        "unresolved": unresolved,
        "results": [asdict(item) for item in results],
        "quality": quality,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import official ETF constituents and evaluate coverage gates."
    )
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--etf-code", action="append", dest="etf_codes")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--max-age-days", type=int, default=7)
    parser.add_argument("--minimum-etf-coverage-pct", type=Decimal, default=Decimal("90"))
    parser.add_argument("--minimum-issuer-coverage-pct", type=Decimal, default=Decimal("90"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if not args.allow_network:
        parser.error("official-source batch retrieval requires --allow-network")
    result = run_constituent_batch_pipeline(
        args.database,
        etf_codes=set(args.etf_codes or ()),
        threshold=ConstituentQualityThreshold(
            max_age_days=args.max_age_days,
            minimum_etf_coverage_pct=args.minimum_etf_coverage_pct,
            minimum_issuer_coverage_pct=args.minimum_issuer_coverage_pct,
        ),
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["quality"]["decision"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
