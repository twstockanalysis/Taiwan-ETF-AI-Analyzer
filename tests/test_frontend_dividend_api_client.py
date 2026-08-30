"""Streamlit 配息 API Client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api_client import (
    APIResponseError,
    fetch_dividend_components,
    fetch_dividend_detail,
    fetch_etf_actual_76w,
    fetch_etf_dividends,
)


class TestFrontendDividendAPIClient(
    unittest.TestCase
):
    """測試前端配息 API Client。"""

    def build_event(
        self,
        dividend_id: int = 2,
    ) -> dict:
        """建立合法配息事件。"""

        return {
            "dividend_id": dividend_id,
            "source_event_id": (
                "official:00918:2026-06"
            ),
            "announcement_date": None,
            "ex_dividend_date": "2026-06-18",
            "record_date": "2026-06-24",
            "payment_date": "2026-07-10",
            "amount_per_unit": 0.7,
            "currency": "TWD",
            "source_id": "official",
            "distribution_period": "2026Q2",
            "distribution_period_source_id": (
                "official"
            ),
            "yield_pct": 2.8,
            "yield_basis": "OFFICIAL",
            "yield_source_id": "official",
            "reference_trade_date": None,
            "reference_close_price": None,
        }

    def build_component(
        self,
        component_id: int = 1,
        dividend_id: int = 2,
        basis: str = "ESTIMATED",
        code: str = (
            "EST_REALIZED_CAPITAL_GAIN"
        ),
        ratio_pct: float | None = 90.0,
    ) -> dict:
        """建立合法配息組成。"""

        return {
            "component_id": component_id,
            "dividend_id": dividend_id,
            "component_code": code,
            "component_basis": basis,
            "component_name": "已實現資本利得",
            "amount_per_unit": None,
            "ratio_pct": ratio_pct,
            "source_id": (
                "twse_etfortune_dividend"
            ),
        }

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_etf_dividends_sends_pagination(
        self,
        mock_get: Mock,
    ) -> None:
        """確認配息歷史網址及分頁參數。"""

        response = Mock()
        response.json.return_value = {
            "etf_code": "00918",
            "total": 1,
            "limit": 10,
            "offset": 20,
            "items": [
                self.build_event(),
            ],
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etf_dividends(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            code=" 00918 ",
            limit=10,
            offset=20,
        )

        self.assertEqual(
            result["etf_code"],
            "00918",
        )

        requested_url = (
            mock_get.call_args.args[0]
        )

        self.assertTrue(
            requested_url.endswith(
                "/api/v1/etfs/"
                "00918/dividends"
            )
        )

        self.assertEqual(
            mock_get.call_args.kwargs[
                "params"
            ],
            {
                "limit": 10,
                "offset": 20,
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_dividend_detail_separates_bases(
        self,
        mock_get: Mock,
    ) -> None:
        """確認單次配息保留預估與實際組成。"""

        response = Mock()
        actual_component = self.build_component(
            component_id=2,
            basis="ACTUAL",
            code="76W",
            ratio_pct=100.0,
        )
        response.json.return_value = {
            **self.build_event(),
            "etf_code": "00918",
            "components": [
                self.build_component(),
                actual_component,
            ],
            "selected_component_basis": "ACTUAL",
            "selected_components": [actual_component],
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_dividend_detail(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            dividend_id=2,
        )

        keys = {
            (
                item["component_basis"],
                item["component_code"],
            )
            for item in result["components"]
        }

        self.assertEqual(
            keys,
            {
                (
                    "ESTIMATED",
                    "EST_REALIZED_CAPITAL_GAIN",
                ),
                (
                    "ACTUAL",
                    "76W",
                ),
            },
        )
        self.assertEqual(
            result["selected_component_basis"],
            "ACTUAL",
        )
        self.assertEqual(
            result["selected_components"][0][
                "component_code"
            ],
            "76W",
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_component_filters_are_normalized(
        self,
        mock_get: Mock,
    ) -> None:
        """確認組成篩選參數正規化。"""

        response = Mock()
        response.json.return_value = {
            "dividend_id": 2,
            "total": 1,
            "items": [
                self.build_component(
                    basis="ACTUAL",
                    code="76W",
                    ratio_pct=0.0,
                ),
            ],
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_dividend_components(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            dividend_id=2,
            component_basis="actual",
            component_code="76w",
            source_id="NOTICE",
        )

        self.assertEqual(
            result["items"][0][
                "ratio_pct"
            ],
            0.0,
        )

        self.assertEqual(
            mock_get.call_args.kwargs[
                "params"
            ],
            {
                "component_basis": "ACTUAL",
                "component_code": "76W",
                "source_id": "notice",
            },
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_actual_76w_keeps_null_semantics(
        self,
        mock_get: Mock,
    ) -> None:
        """確認缺資料保持 None，不轉成 0%。"""

        response = Mock()
        response.json.return_value = {
            "etf_code": "00918",
            "total_dividend_count": 3,
            "actual_76w_record_count": 0,
            "full_76w_count": 0,
            "latest_76w_ratio_pct": None,
            "average_76w_ratio_pct": None,
            "items": [],
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etf_actual_76w(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            code="00918",
        )

        self.assertIsNone(
            result[
                "latest_76w_ratio_pct"
            ]
        )

        self.assertIsNone(
            result[
                "average_76w_ratio_pct"
            ]
        )

        self.assertEqual(
            result[
                "actual_76w_record_count"
            ],
            0,
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_actual_76w_accepts_zero_ratio(
        self,
        mock_get: Mock,
    ) -> None:
        """確認正式 0% 與缺資料可以區分。"""

        item = {
            **self.build_event(),
            "component_amount_per_unit": 0.0,
            "ratio_pct": 0.0,
            "source_id": (
                "official_distribution_notice"
            ),
        }

        response = Mock()
        response.json.return_value = {
            "etf_code": "00918",
            "total_dividend_count": 1,
            "actual_76w_record_count": 1,
            "full_76w_count": 0,
            "latest_76w_ratio_pct": 0.0,
            "average_76w_ratio_pct": 0.0,
            "items": [
                item,
            ],
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_etf_actual_76w(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            code="00918",
        )

        self.assertEqual(
            result[
                "latest_76w_ratio_pct"
            ],
            0.0,
        )

        self.assertEqual(
            result["items"][0][
                "ratio_pct"
            ],
            0.0,
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_fetch_76w_accepts_estimated_composite_fallback(
        self,
        mock_get: Mock,
    ) -> None:
        """正式 76W 缺少時保留 missing，另接受 68% 替代分析。"""

        response = Mock()
        response.json.return_value = {
            "etf_code": "0050",
            "total_dividend_count": 1,
            "actual_76w_record_count": 0,
            "full_76w_count": 0,
            "latest_76w_ratio_pct": None,
            "average_76w_ratio_pct": None,
            "analysis_record_count": 1,
            "analysis_actual_count": 0,
            "analysis_estimated_fallback_count": 1,
            "full_realized_gain_count": 0,
            "latest_realized_gain_ratio_pct": 68.0,
            "average_realized_gain_ratio_pct": 68.0,
            "latest_analysis_basis": "ESTIMATED_FALLBACK",
            "items": [],
        }
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = fetch_etf_actual_76w(
            api_base_url="http://127.0.0.1:8000",
            code="0050",
        )

        self.assertEqual(result["actual_76w_record_count"], 0)
        self.assertIsNone(result["latest_76w_ratio_pct"])
        self.assertEqual(result["analysis_record_count"], 1)
        self.assertEqual(result["latest_realized_gain_ratio_pct"], 68.0)
        self.assertEqual(result["latest_analysis_basis"], "ESTIMATED_FALLBACK")

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_estimated_gain_is_not_renamed_76w(
        self,
        mock_get: Mock,
    ) -> None:
        """確認 API Client 保留預估資本利得代碼。"""

        response = Mock()
        estimated_component = self.build_component()
        response.json.return_value = {
            **self.build_event(),
            "etf_code": "00918",
            "components": [
                estimated_component,
            ],
            "selected_component_basis": (
                "ESTIMATED_FALLBACK"
            ),
            "selected_components": [
                estimated_component,
            ],
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_dividend_detail(
            api_base_url=(
                "http://127.0.0.1:8000"
            ),
            dividend_id=2,
        )

        self.assertEqual(
            result["components"][0][
                "component_code"
            ],
            "EST_REALIZED_CAPITAL_GAIN",
        )

        self.assertNotEqual(
            result["components"][0][
                "component_code"
            ],
            "76W",
        )

    @patch(
        "frontend.api_client.httpx.get"
    )
    def test_invalid_component_ratio_is_rejected(
        self,
        mock_get: Mock,
    ) -> None:
        """確認超過 100% 的組成被拒絕。"""

        response = Mock()
        response.json.return_value = {
            **self.build_event(),
            "etf_code": "00918",
            "components": [
                self.build_component(
                    ratio_pct=101.0,
                ),
            ],
        }
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        with self.assertRaises(
            APIResponseError
        ):
            fetch_dividend_detail(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                dividend_id=2,
            )

    def test_invalid_dividend_parameters(
        self,
    ) -> None:
        """確認不合法查詢參數在送出前被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            fetch_etf_dividends(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                code="00918",
                limit=0,
            )

        with self.assertRaises(
            ValueError
        ):
            fetch_dividend_components(
                api_base_url=(
                    "http://127.0.0.1:8000"
                ),
                dividend_id=1,
                component_basis="UNKNOWN",
            )


if __name__ == "__main__":
    unittest.main()
