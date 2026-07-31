"""Streamlit 配息資料品質 API Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_actual_dividend_coverage,
    fetch_dividend_review_queue,
    fetch_dividend_review_queue_item,
)


class TestFrontendDividendQualityAPIClient(
    unittest.TestCase
):
    """測試正式配息品質 API Client。"""

    def build_coverage(
        self,
        etf_code: str | None = None,
        total: int = 4,
    ) -> dict:
        """建立合法覆蓋率回應。"""

        if total == 0:
            return {
                "etf_code": etf_code,
                "total_dividend_count": 0,
                "estimated_component_event_count": 0,
                "actual_component_event_count": 0,
                "actual_76w_event_count": 0,
                "source_document_event_count": 0,
                "missing_actual_component_event_count": 0,
                "missing_source_document_event_count": 0,
                "actual_component_coverage_pct": None,
                "actual_76w_coverage_pct": None,
                "source_document_coverage_pct": None,
            }

        return {
            "etf_code": etf_code,
            "total_dividend_count": 4,
            "estimated_component_event_count": 3,
            "actual_component_event_count": 2,
            "actual_76w_event_count": 1,
            "source_document_event_count": 1,
            "missing_actual_component_event_count": 2,
            "missing_source_document_event_count": 3,
            "actual_component_coverage_pct": 50.0,
            "actual_76w_coverage_pct": 25.0,
            "source_document_coverage_pct": 25.0,
        }

    def build_queue_item(
        self,
        queue_id: int = 7,
        status: str = "PENDING",
        issue_type: str = (
            "MISSING_SOURCE_DOCUMENT"
        ),
    ) -> dict:
        """建立合法待處理項目。"""

        return {
            "queue_id": queue_id,
            "dividend_id": 233,
            "etf_code": "00900",
            "source_event_id": (
                "twse_etfortune_dividend:"
                "00900:2026-02-25"
            ),
            "ex_dividend_date": "2026-02-25",
            "amount_per_unit": 0.075,
            "currency": "TWD",
            "issue_type": issue_type,
            "suggested_source_id": (
                "manual_actual_dividend_notice"
            ),
            "priority": 20,
            "status": status,
            "notes": None,
            "resolution_document_id": None,
            "last_evaluated_at": (
                "2026-07-31T07:55:28+00:00"
            ),
            "resolved_at": None,
            "created_at": (
                "2026-07-31T07:55:28+00:00"
            ),
            "updated_at": (
                "2026-07-31T07:55:28+00:00"
            ),
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_global_coverage(
        self,
        mock_get: Mock,
    ) -> None:
        """確認全站覆蓋率網址與空參數。"""

        response = Mock()
        response.json.return_value = (
            self.build_coverage()
        )
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = fetch_actual_dividend_coverage(
            "http://127.0.0.1:8000"
        )

        self.assertEqual(
            result["actual_76w_coverage_pct"],
            25.0,
        )

        self.assertTrue(
            mock_get.call_args.args[0].endswith(
                "/api/v1/data-quality/dividends/"
                "actual-coverage"
            )
        )

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {},
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_etf_coverage_normalizes_code(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 ETF 代號正規化並送入查詢參數。"""

        response = Mock()
        response.json.return_value = (
            self.build_coverage(
                etf_code="00900"
            )
        )
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = fetch_actual_dividend_coverage(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            etf_code=" 00900 ",
        )

        self.assertEqual(
            result["etf_code"],
            "00900",
        )

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {
                "etf_code": "00900",
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_empty_coverage_preserves_null_rates(
        self,
        mock_get: Mock,
    ) -> None:
        """確認零事件時覆蓋率保持 None。"""

        response = Mock()
        response.json.return_value = (
            self.build_coverage(
                etf_code="0050",
                total=0,
            )
        )
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = fetch_actual_dividend_coverage(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            etf_code="0050",
        )

        self.assertIsNone(
            result[
                "actual_component_coverage_pct"
            ]
        )

        self.assertIsNone(
            result["actual_76w_coverage_pct"]
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_queue_normalizes_filters(
        self,
        mock_get: Mock,
    ) -> None:
        """確認狀態、問題類型與 ETF 篩選正規化。"""

        response = Mock()
        response.json.return_value = {
            "total": 1,
            "limit": 10,
            "offset": 20,
            "items": [
                self.build_queue_item(),
            ],
        }
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = fetch_dividend_review_queue(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            status="pending",
            etf_code=" 00900 ",
            issue_type=(
                "missing_source_document"
            ),
            limit=10,
            offset=20,
        )

        self.assertEqual(
            result["items"][0]["queue_id"],
            7,
        )

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {
                "limit": 10,
                "offset": 20,
                "status": "PENDING",
                "etf_code": "00900",
                "issue_type": (
                    "MISSING_SOURCE_DOCUMENT"
                ),
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_queue_item_uses_id(
        self,
        mock_get: Mock,
    ) -> None:
        """確認單筆明細網址與 ID 驗證。"""

        response = Mock()
        response.json.return_value = (
            self.build_queue_item(
                queue_id=472
            )
        )
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = (
            fetch_dividend_review_queue_item(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                queue_id=472,
            )
        )

        self.assertEqual(
            result["queue_id"],
            472,
        )

        self.assertTrue(
            mock_get.call_args.args[0].endswith(
                "/review-queue/472"
            )
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_inconsistent_coverage_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認缺失數與覆蓋數矛盾時被拒絕。"""

        payload = self.build_coverage()
        payload[
            "missing_actual_component_event_count"
        ] = 1

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_actual_dividend_coverage(
                "http://127.0.0.1:8000"
            )

    def test_invalid_quality_parameters(
        self,
    ) -> None:
        """確認不合法參數在送出前被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            fetch_dividend_review_queue(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                status="UNKNOWN",
            )

        with self.assertRaises(
            ValueError
        ):
            fetch_dividend_review_queue(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                issue_type="UNKNOWN",
            )

        with self.assertRaises(
            ValueError
        ):
            fetch_dividend_review_queue_item(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                queue_id=0,
            )


if __name__ == "__main__":
    unittest.main()
