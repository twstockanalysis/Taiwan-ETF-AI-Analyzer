"""M12-6 launch-data decision tests."""

import unittest
from datetime import datetime, timezone

from deployment.launch_data_check import evaluate_launch_data


class TestLaunchDataCheck(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluated_at = datetime(2026, 8, 12, tzinfo=timezone.utc)
        self.summary = {
            "total_dividend_count": 10,
            "actual_component_event_count": 1,
            "actual_76w_event_count": 1,
            "source_document_event_count": 1,
        }

    def test_ready_when_all_thresholds_pass(self) -> None:
        result = evaluate_launch_data(
            self.summary,
            evaluated_at=self.evaluated_at,
        )

        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(all(item["passed"] for item in result["checks"]))

    def test_no_go_when_reviewed_coverage_is_zero(self) -> None:
        summary = {
            **self.summary,
            "actual_component_event_count": 0,
            "actual_76w_event_count": 0,
            "source_document_event_count": 0,
        }

        result = evaluate_launch_data(summary, evaluated_at=self.evaluated_at)

        self.assertEqual(result["decision"], "NO_GO")
        self.assertEqual(result["exit_code"], 1)
        self.assertIsNone(result["limited_coverage_approval"])

    def test_limited_launch_requires_named_approval_and_reason(self) -> None:
        summary = {
            **self.summary,
            "actual_76w_event_count": 0,
        }

        result = evaluate_launch_data(
            summary,
            limited_coverage_approved_by="site owner",
            limited_coverage_reason="Visible limited-data disclosure approved",
            evaluated_at=self.evaluated_at,
        )

        self.assertEqual(result["decision"], "LIMITED_APPROVED")
        self.assertEqual(result["exit_code"], 0)

    def test_partial_limited_approval_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires both"):
            evaluate_launch_data(
                self.summary,
                limited_coverage_approved_by="site owner",
                evaluated_at=self.evaluated_at,
            )

    def test_zero_dividend_events_does_not_pass(self) -> None:
        summary = {
            **self.summary,
            "total_dividend_count": 0,
        }

        result = evaluate_launch_data(summary, evaluated_at=self.evaluated_at)

        self.assertEqual(result["decision"], "NO_GO")
        self.assertFalse(result["checks"][0]["passed"])


if __name__ == "__main__":
    unittest.main()
