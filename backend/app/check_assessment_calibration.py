"""輸出 V4-1 評等覆蓋與門檻敏感度 JSON；唯讀且不持久化。"""

from __future__ import annotations

import argparse
from datetime import date
import json

from backend.app.models.market_eligibility import MarketEligibilityIndexRequest
from backend.app.services.assessment_calibration import (
    build_assessment_calibration_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--analysis-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--history-years", type=int, default=3, choices=range(1, 11))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    request = MarketEligibilityIndexRequest(
        target_after_tax_cash_twd=0,
        target_months=list(range(1, 13)),
        existing_holdings=[],
        history_years=args.history_years,
        cash_deduction_rate_pct=0,
    )
    report = build_assessment_calibration_report(
        request,
        args.database,
        as_of_date=args.analysis_date,
    )
    print(
        json.dumps(
            report.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

