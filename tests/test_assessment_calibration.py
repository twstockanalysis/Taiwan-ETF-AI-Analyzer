"""V4-1 校準報告不洩漏個別原始分數的測試。"""

import json
import unittest
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.models.market_eligibility import MarketEligibilityIndexRequest
from backend.app.models.quality_grade import ETFHistoricalQualityGrade
from backend.app.services.assessment_calibration import (
    build_assessment_calibration_report,
)


class TestAssessmentCalibration(unittest.TestCase):
    @patch(
        "backend.app.services.assessment_calibration."
        "build_market_eligibility_index"
    )
    def test_report_blocks_undersized_saturated_sample(self, build_index) -> None:
        public_items = [
            SimpleNamespace(
                historical_quality_grade=ETFHistoricalQualityGrade(
                    status="UNRATED",
                    evidence_period_years=3,
                    unavailable_evidence=["校準尚未完成"],
                    explanation="暫不評等。",
                )
            )
            for _ in range(10)
        ]
        internal_items = [
            SimpleNamespace(
                quality_score=Decimal("95"),
                quality_grade_eligible=True,
                quality_missing=(),
                quality_components=(
                    SimpleNamespace(
                        code="AFTER_TAX_TOTAL_RETURN",
                        score=Decimal("100"),
                        observed_value=Decimal("60"),
                    ),
                    SimpleNamespace(
                        code="DOWNSIDE_RETURN",
                        score=Decimal("90"),
                        observed_value=Decimal("-4"),
                    ),
                ),
            )
            for _ in range(10)
        ]
        build_index.return_value = SimpleNamespace(
            response=SimpleNamespace(
                analysis_date=date(2026, 8, 26),
                snapshot_id="sha256:" + "a" * 64,
                universe_count=100,
                supported_product_count=80,
                candidates=public_items,
            ),
            internal_candidates=tuple(internal_items),
        )
        request = MarketEligibilityIndexRequest(
            target_after_tax_cash_twd=0,
            target_months=[1],
            existing_holdings=[],
            history_years=3,
            cash_deduction_rate_pct=0,
        )

        report = build_assessment_calibration_report(
            request,
            "unused.db",
            as_of_date=date(2026, 8, 26),
        )
        payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)

        self.assertFalse(report.publication_ready)
        self.assertEqual(report.provisional_rated_count, 10)
        self.assertEqual(report.published_rated_count, 0)
        self.assertEqual(report.provisional_grade_counts["A+"], 10)
        self.assertNotIn("quality_score", payload)
        self.assertNotIn("confidence", payload)
        self.assertEqual(
            {item.code: item.status.value for item in report.factor_decisions}[
                "FILL_CAPABILITY"
            ],
            "DEFERRED",
        )


if __name__ == "__main__":
    unittest.main()
