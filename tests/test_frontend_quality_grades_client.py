"""V4-5 公開 ETF 歷史品質評等 client 測試。"""

import unittest
from unittest.mock import patch

from frontend.api.errors import APIResponseError
from frontend.api.quality_grades import (
    fetch_historical_quality_grades,
    quality_grade_lookup,
    validate_historical_quality_grade,
)


def grade(status: str = "UNRATED", letter: str | None = None) -> dict:
    return {
        "methodology": "DETERMINISTIC_QUALITY_GRADE_V4_1",
        "score_methodology": "DETERMINISTIC_MULTI_SCORE_V2",
        "threshold_version": "FIXED_THRESHOLDS_V1",
        "status": status,
        "grade": letter,
        "evidence_period_years": 3,
        "strengths": [],
        "risks": [],
        "unavailable_evidence": ["樣本不足"] if status == "UNRATED" else [],
        "explanation": "歷史品質評等。",
    }


class TestFrontendQualityGradesClient(unittest.TestCase):
    def test_fetch_preserves_requested_order_and_builds_lookup(self) -> None:
        payload = {
            "methodology": "DETERMINISTIC_QUALITY_GRADE_V4_1",
            "analysis_date": "2026-08-26",
            "history_years": 3,
            "items": [
                {"etf_code": "0056", "historical_quality_grade": grade()},
                {
                    "etf_code": "0050",
                    "historical_quality_grade": grade("RATED", "A"),
                },
            ],
        }
        with patch(
            "frontend.api.quality_grades.get_json",
            return_value=payload,
        ) as get_json:
            result = fetch_historical_quality_grades(
                "http://127.0.0.1:8000",
                ["0056", "0050"],
            )

        self.assertEqual(
            get_json.call_args.kwargs["params"]["codes"],
            "0056,0050",
        )
        self.assertEqual(quality_grade_lookup(result)["0050"]["grade"], "A")

    def test_validator_rejects_internal_score_or_invalid_unrated_grade(self) -> None:
        scored = grade("RATED", "A")
        scored["quality_score"] = 90
        with self.assertRaises(APIResponseError):
            validate_historical_quality_grade(scored)

        invalid_unrated = grade("UNRATED", "F")
        with self.assertRaises(APIResponseError):
            validate_historical_quality_grade(invalid_unrated)


if __name__ == "__main__":
    unittest.main()
