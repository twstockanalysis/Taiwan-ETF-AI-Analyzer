"""Streamlit 首頁系統總覽 API Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_system_overview,
)


def build_valid_overview() -> dict:
    """建立合法首頁總覽回應。"""

    return {
        "api_status": "healthy",
        "database_type": "SQLite",
        "etfs": {
            "total_count": 4,
            "active_count": 1,
            "passive_count": 3,
            "bond_count": 1,
            "non_bond_count": 3,
            "latest_master_import_at": (
                "2026-07-30T00:05:00+00:00"
            ),
        },
        "performance": {
            "metric_code": "PRICE_RETURN",
            "source_id": "twse_stock_day",
            "etf_count": 2,
            "total_etf_count": 4,
            "coverage_pct": 50.0,
            "latest_as_of_date": "2026-07-30",
            "periods": [
                {
                    "period_code": "1M",
                    "etf_count": 2,
                    "coverage_pct": 50.0,
                    "latest_as_of_date": (
                        "2026-07-30"
                    ),
                },
                {
                    "period_code": "3M",
                    "etf_count": 1,
                    "coverage_pct": 25.0,
                    "latest_as_of_date": (
                        "2026-07-29"
                    ),
                },
                {
                    "period_code": "6M",
                    "etf_count": 2,
                    "coverage_pct": 50.0,
                    "latest_as_of_date": (
                        "2026-07-30"
                    ),
                },
                {
                    "period_code": "1Y",
                    "etf_count": 1,
                    "coverage_pct": 25.0,
                    "latest_as_of_date": (
                        "2026-07-29"
                    ),
                },
            ],
        },
        "dividends": {
            "event_count": 2,
            "etf_count": 2,
            "latest_event_date": "2026-08-10",
            "actual_component_event_count": 1,
            "actual_76w_event_count": 1,
            "source_document_event_count": 1,
            "actual_component_coverage_pct": (
                50.0
            ),
            "actual_76w_coverage_pct": 50.0,
            "source_document_coverage_pct": (
                50.0
            ),
            (
                "latest_actual_"
                "source_document_date"
            ): "2026-07-31",
        },
        "recent_import_batches": [
            {
                "batch_id": 4,
                "pipeline_name": (
                    "actual_dividend_pipeline"
                ),
                "source_id": "official_notice",
                "endpoint_id": "reviewed_json",
                "started_at": (
                    "2026-07-31T02:00:00+00:00"
                ),
                "completed_at": (
                    "2026-07-31T02:02:00+00:00"
                ),
                "status": "success",
                "raw_record_count": 1,
                "accepted_record_count": 1,
                "rejected_record_count": 0,
                "inserted_record_count": 1,
                "updated_record_count": 0,
                "error_message": None,
            },
        ],
    }


class TestFrontendSystemOverviewAPIClient(
    unittest.TestCase
):
    """測試總覽 Endpoint 與回應契約。"""

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_system_overview(
        self,
        mock_get: Mock,
    ) -> None:
        """確認網址及合法回應可正常解析。"""

        response = Mock()
        response.json.return_value = (
            build_valid_overview()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_system_overview(
            "http://127.0.0.1:8000"
        )

        self.assertEqual(
            result["etfs"]["total_count"],
            4,
        )

        self.assertEqual(
            result["performance"][
                "periods"
            ][0]["period_code"],
            "1M",
        )

        requested_url = (
            mock_get.call_args.args[0]
        )

        self.assertTrue(
            requested_url.endswith(
                "/api/v1/system/overview"
            )
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_inconsistent_etf_counts_are_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認分類數量與總數不一致時拒絕回應。"""

        payload = build_valid_overview()

        payload["etfs"][
            "active_count"
        ] = 2

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_system_overview(
                "http://127.0.0.1:8000"
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_missing_performance_period_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認績效期間必須完整且不重複。"""

        payload = build_valid_overview()

        payload["performance"][
            "periods"
        ] = payload["performance"][
            "periods"
        ][:-1]

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_system_overview(
                "http://127.0.0.1:8000"
            )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_empty_overview_requires_null_rates(
        self,
        mock_get: Mock,
    ) -> None:
        """確認零分母時不得偽造 0% 覆蓋率。"""

        payload = build_valid_overview()

        payload["etfs"] = {
            "total_count": 0,
            "active_count": 0,
            "passive_count": 0,
            "bond_count": 0,
            "non_bond_count": 0,
            "latest_master_import_at": None,
        }

        payload["performance"][
            "etf_count"
        ] = 0
        payload["performance"][
            "total_etf_count"
        ] = 0
        payload["performance"][
            "coverage_pct"
        ] = 0.0
        payload["performance"][
            "latest_as_of_date"
        ] = None

        for item in payload[
            "performance"
        ]["periods"]:
            item["etf_count"] = 0
            item["coverage_pct"] = None
            item["latest_as_of_date"] = None

        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_system_overview(
                "http://127.0.0.1:8000"
            )


if __name__ == "__main__":
    unittest.main()
