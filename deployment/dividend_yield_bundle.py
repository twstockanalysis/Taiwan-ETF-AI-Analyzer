"""Export and import a reviewable dividend-yield collaboration bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from backend.app.database.connection import get_connection
from backend.app.models.etf_analysis import (
    ETFDividendSummaryMetricRecord,
)
from backend.app.repositories.dividend_repository import (
    upsert_dividend_summary_metrics,
)


BUNDLE_FORMAT_VERSION = 1
BUNDLE_DATASET = "goodcat-v5-1b-dividend-yields"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decimal_text(value: object) -> str:
    decimal_value = Decimal(str(value))
    normalized = format(decimal_value.normalize(), "f")
    return "0" if normalized == "-0" else normalized


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def export_dividend_yield_bundle(
    database_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
) -> dict[str, Any]:
    """Export traced yield fields without database IDs or local paths."""

    database = Path(database_path).resolve()
    bundle = Path(bundle_path).resolve()
    manifest = Path(manifest_path).resolve()
    if not database.is_file():
        raise FileNotFoundError(f"database does not exist: {database}")
    for output in (bundle, manifest):
        if output.exists():
            raise FileExistsError(f"output already exists: {output}")

    connection = get_connection(database)
    try:
        integrity = str(
            connection.execute("PRAGMA integrity_check;").fetchone()[0]
        )
        foreign_key_violations = len(
            connection.execute("PRAGMA foreign_key_check;").fetchall()
        )
        if integrity != "ok" or foreign_key_violations:
            raise ValueError(
                "source database failed integrity or foreign-key checks"
            )

        rows = connection.execute(
            """
            SELECT
                d.etf_code,
                d.source_id AS event_source_id,
                d.source_event_id,
                d.ex_dividend_date,
                d.amount_per_unit,
                d.currency,
                m.yield_pct,
                m.yield_basis,
                m.yield_source_id,
                m.reference_trade_date,
                m.reference_close_price
            FROM etf_dividend_summary_metric AS m
            JOIN etf_dividend AS d
              ON d.id = m.dividend_id
            WHERE m.yield_pct IS NOT NULL
            ORDER BY
                d.etf_code,
                d.ex_dividend_date,
                d.source_id,
                d.source_event_id;
            """
        ).fetchall()
    finally:
        connection.close()

    records = [
        {
            "amount_per_unit": _decimal_text(row["amount_per_unit"]),
            "currency": row["currency"],
            "etf_code": row["etf_code"],
            "event_source_id": row["event_source_id"],
            "ex_dividend_date": row["ex_dividend_date"],
            "reference_close_price": (
                _decimal_text(row["reference_close_price"])
                if row["reference_close_price"] is not None
                else None
            ),
            "reference_trade_date": row["reference_trade_date"],
            "source_event_id": row["source_event_id"],
            "yield_basis": row["yield_basis"],
            "yield_pct": _decimal_text(row["yield_pct"]),
            "yield_source_id": row["yield_source_id"],
        }
        for row in rows
    ]
    payload = {
        "dataset": BUNDLE_DATASET,
        "format_version": BUNDLE_FORMAT_VERSION,
        "records": records,
    }
    _write_json(bundle, payload)

    basis_counts = Counter(
        str(record["yield_basis"])
        for record in records
    )
    manifest_payload = {
        "bundle_file": bundle.name,
        "bundle_sha256": _sha256(bundle),
        "dataset": BUNDLE_DATASET,
        "format_version": BUNDLE_FORMAT_VERSION,
        "record_count": len(records),
        "source_database_sha256": _sha256(database),
        "source_database_size": database.stat().st_size,
        "source_foreign_key_violation_count": foreign_key_violations,
        "source_integrity_check": integrity,
        "yield_basis_counts": dict(sorted(basis_counts.items())),
    }
    _write_json(manifest, manifest_payload)
    return manifest_payload


def _load_verified_bundle(
    bundle_path: Path,
    manifest_path: Path,
) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("bundle_file") != bundle_path.name:
        raise ValueError("manifest bundle filename does not match")
    if manifest.get("bundle_sha256") != _sha256(bundle_path):
        raise ValueError("bundle SHA-256 does not match manifest")

    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    if payload.get("format_version") != BUNDLE_FORMAT_VERSION:
        raise ValueError("unsupported bundle format version")
    if payload.get("dataset") != BUNDLE_DATASET:
        raise ValueError("unexpected bundle dataset")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("bundle records must be a list")
    if manifest.get("record_count") != len(records):
        raise ValueError("manifest record count does not match bundle")
    return records


def import_dividend_yield_bundle(
    database_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
) -> dict[str, int]:
    """Apply verified yields only when stable event fingerprints match."""

    database = Path(database_path).resolve()
    bundle = Path(bundle_path).resolve()
    manifest = Path(manifest_path).resolve()
    if not database.is_file():
        raise FileNotFoundError(f"database does not exist: {database}")

    records = _load_verified_bundle(bundle, manifest)
    seen_keys: set[tuple[str, str]] = set()
    metrics: list[ETFDividendSummaryMetricRecord] = []
    connection = get_connection(database)
    try:
        if connection.execute("PRAGMA integrity_check;").fetchone()[0] != "ok":
            raise ValueError("target database failed integrity check")
        if connection.execute("PRAGMA foreign_key_check;").fetchall():
            raise ValueError("target database has foreign-key violations")

        for record in records:
            if not isinstance(record, dict):
                raise ValueError("bundle record must be an object")
            key = (
                str(record.get("event_source_id", "")),
                str(record.get("source_event_id", "")),
            )
            if not all(key) or key in seen_keys:
                raise ValueError(f"invalid or duplicate event key: {key}")
            seen_keys.add(key)

            row = connection.execute(
                """
                SELECT
                    id,
                    etf_code,
                    ex_dividend_date,
                    amount_per_unit,
                    currency
                FROM etf_dividend
                WHERE source_id = ?
                  AND source_event_id = ?;
                """,
                key,
            ).fetchone()
            if row is None:
                raise KeyError(
                    "target database is missing dividend event: "
                    f"{key[0]}/{key[1]}"
                )

            expected_fingerprint = (
                str(record.get("etf_code")),
                record.get("ex_dividend_date"),
                _decimal_text(record.get("amount_per_unit")),
                str(record.get("currency")),
            )
            actual_fingerprint = (
                row["etf_code"],
                row["ex_dividend_date"],
                _decimal_text(row["amount_per_unit"]),
                row["currency"],
            )
            if actual_fingerprint != expected_fingerprint:
                raise ValueError(
                    "dividend event fingerprint mismatch: "
                    f"{key[0]}/{key[1]}"
                )

            metrics.append(
                ETFDividendSummaryMetricRecord(
                    dividend_id=int(row["id"]),
                    yield_pct=record.get("yield_pct"),
                    yield_basis=record.get("yield_basis"),
                    yield_source_id=record.get("yield_source_id"),
                    reference_trade_date=record.get(
                        "reference_trade_date"
                    ),
                    reference_close_price=record.get(
                        "reference_close_price"
                    ),
                )
            )
    finally:
        connection.close()

    summary = upsert_dividend_summary_metrics(metrics, database)
    return {
        "inserted_records": summary.inserted_records,
        "total_records": summary.total_records,
        "updated_records": summary.updated_records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Share traced dividend yields without committing SQLite",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--database", required=True, type=Path)
    export_parser.add_argument("--bundle", required=True, type=Path)
    export_parser.add_argument("--manifest", required=True, type=Path)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--database", required=True, type=Path)
    import_parser.add_argument("--bundle", required=True, type=Path)
    import_parser.add_argument("--manifest", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "export":
        result = export_dividend_yield_bundle(
            args.database,
            args.bundle,
            args.manifest,
        )
    else:
        result = import_dividend_yield_bundle(
            args.database,
            args.bundle,
            args.manifest,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
