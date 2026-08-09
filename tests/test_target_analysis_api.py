"""單一 ETF 目標分析 API 契約測試。"""

from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest
from unittest.mock import ANY, patch

from fastapi.testclient import TestClient

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.main import create_app
from backend.app.models.cash_flow_analysis import (
    AnalysisMode,
    CalculationContext,
)
from backend.app.models.target_analysis import (
    TargetAnalysisRequest,
    TargetAnalysisStatus,
    TargetAnalysisUnavailableField,
    TargetAnalysisWarning,
    TargetAnalysisWarningCode,
)
from backend.app.services.target_analysis_calculator import (
    calculate_target_analysis as run_target_analysis,
)
from backend.app.services.target_analysis_data import (
    TargetAnalysisData,
)


class TestTargetAnalysisAPI(unittest.TestCase):
    """測試目標分析 API 公開契約。"""

    def setUp(self) -> None:
        """建立測試應用程式。"""

        self.database_path = Path(
            "target-analysis-test.db"
        )
        self.application = create_app()
        self.application.dependency_overrides[
            get_database_path
        ] = lambda: self.database_path

        self.client = TestClient(
            self.application
        )

    def tearDown(self) -> None:
        """關閉測試資源。"""

        self.client.close()
        self.application.dependency_overrides.clear()

    @staticmethod
    def _valid_request() -> dict:
        """建立有效的目標分析請求。"""

        return {
            "held_units": 1000,
            "unit_price": "35.5",
            "monthly_after_tax_target": "3000",
            "analysis_years": 10,
            "history_years": 3,
            "cash_deduction_rate_pct": "5",
        }

    def test_openapi_contains_target_analysis_post_path(
        self,
    ) -> None:
        """確認 OpenAPI 登錄目標分析 POST 端點。"""

        path = (
            "/api/v1/etfs/{code}/target-analysis"
        )

        paths = self.application.openapi()["paths"]

        self.assertIn(
            path,
            paths,
        )
        self.assertIn(
            "post",
            paths[path],
        )

    def test_openapi_uses_request_and_result_models(
        self,
    ) -> None:
        """確認 OpenAPI 使用正式輸入與輸出模型。"""

        operation = self.application.openapi()[
            "paths"
        ][
            "/api/v1/etfs/{code}/target-analysis"
        ][
            "post"
        ]

        self.assertIn(
            "requestBody",
            operation,
        )

        request_schema = operation[
            "requestBody"
        ][
            "content"
        ][
            "application/json"
        ][
            "schema"
        ]

        response_schema = operation[
            "responses"
        ][
            "200"
        ][
            "content"
        ][
            "application/json"
        ][
            "schema"
        ]

        self.assertEqual(
            request_schema,
            {
                "$ref": (
                    "#/components/schemas/"
                    "TargetAnalysisRequest"
                ),
            },
        )
        self.assertEqual(
            response_schema,
            {
                "$ref": (
                    "#/components/schemas/"
                    "TargetAnalysisResult"
                ),
            },
        )

    def test_unknown_request_field_returns_422(
        self,
    ) -> None:
        """確認公開輸入契約拒絕未知欄位。"""

        response = self.client.post(
            "/api/v1/etfs/0056/target-analysis",
            json={
                **self._valid_request(),
                "unexpected": "not-allowed",
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

    @patch(
        "backend.app.api.routers.target_analysis."
        "get_etf_by_code",
    )
    def test_unknown_etf_returns_404(
        self,
        mock_get_etf_by_code,
    ) -> None:
        """確認不存在的 ETF 回傳 404。"""

        mock_get_etf_by_code.return_value = None

        response = self.client.post(
            "/api/v1/etfs/0056/target-analysis",
            json=self._valid_request(),
        )

        self.assertEqual(
            response.status_code,
            404,
        )
        self.assertEqual(
            response.json(),
            {
                "detail": "找不到 ETF：0056",
            },
        )
        mock_get_etf_by_code.assert_called_once_with(
            "0056",
            self.database_path,
        )

    @patch(
        "backend.app.api.routers.target_analysis."
        "calculate_target_analysis",
        create=True,
    )
    @patch(
        "backend.app.api.routers.target_analysis."
        "load_target_analysis_data",
        create=True,
    )
    @patch(
        "backend.app.api.routers.target_analysis."
        "get_etf_by_code",
    )
    def test_existing_etf_returns_calculated_result(
        self,
        mock_get_etf_by_code,
        mock_load_target_analysis_data,
        mock_calculate_target_analysis,
    ) -> None:
        """確認有效請求載入資料並呼叫目標分析服務。"""

        request_payload = {
            **self._valid_request(),
            "unit_price": "35.5",
            "history_years": 3,
        }
        parsed_request = TargetAnalysisRequest(
            **request_payload
        )
        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2023, 1, 1),
            period_end=date(2025, 12, 31),
        )
        loaded_data = TargetAnalysisData(
            monthly_income={
                "analysis_currency": "TWD",
                "has_mixed_currencies": False,
                "lookback_years": 3,
                "window_start_date": date(
                    2023,
                    1,
                    1,
                ),
                "as_of_date": date(
                    2025,
                    12,
                    31,
                ),
                "total_amount_per_unit": 3.216,
            },
            dividends=[],
            selected_performance={
                "period_code": "1Y",
                "return_pct": 4.0,
                "as_of_date": date(
                    2025,
                    12,
                    31,
                ),
            },
            warnings=[],
            unavailable_fields=[],
        )
        expected_result = run_target_analysis(
            parsed_request,
            context=context,
            gross_distribution_cash=Decimal(
                "1072"
            ),
            distribution_tax=None,
            supplementary_premium=None,
            other_distribution_costs=None,
            annual_gross_cash_rate_pct=Decimal(
                "3.019718"
            ),
            annual_price_return_pct=Decimal(
                "4"
            ),
        )

        mock_get_etf_by_code.return_value = {
            "code": "0056",
            "name": "元大高股息",
        }
        mock_load_target_analysis_data.return_value = (
            loaded_data
        )
        mock_calculate_target_analysis.return_value = (
            expected_result
        )

        response = self.client.post(
            "/api/v1/etfs/0056/target-analysis",
            json=request_payload,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            expected_result.model_dump(
                mode="json"
            ),
        )

        mock_get_etf_by_code.assert_called_once_with(
            "0056",
            self.database_path,
        )
        mock_load_target_analysis_data.assert_called_once_with(
            etf_code="0056",
            database_path=self.database_path,
            history_years=3,
            as_of_date=ANY,
        )

        load_call = (
            mock_load_target_analysis_data.call_args
        )
        self.assertIsInstance(
            load_call.kwargs["as_of_date"],
            date,
        )

        mock_calculate_target_analysis.assert_called_once_with(
            ANY,
            context=context,
            gross_distribution_cash=Decimal(
                "1072"
            ),
            distribution_tax=None,
            supplementary_premium=None,
            other_distribution_costs=None,
            annual_gross_cash_rate_pct=Decimal(
                "3.019718"
            ),
            annual_price_return_pct=Decimal(
                "4"
            ),
        )

        calculated_request = (
            mock_calculate_target_analysis
            .call_args.args[0]
        )
        self.assertEqual(
            calculated_request,
            parsed_request,
        )


    @patch(
        "backend.app.api.routers.target_analysis."
        "calculate_target_analysis",
    )
    @patch(
        "backend.app.api.routers.target_analysis."
        "load_target_analysis_data",
    )
    @patch(
        "backend.app.api.routers.target_analysis."
        "get_etf_by_code",
    )
    def test_data_quality_information_is_merged(
        self,
        mock_get_etf_by_code,
        mock_load_target_analysis_data,
        mock_calculate_target_analysis,
    ) -> None:
        """確認資料品質資訊合併且不修改計算器結果。"""

        request_payload = {
            **self._valid_request(),
            "unit_price": "35.5",
            "history_years": 3,
        }
        parsed_request = TargetAnalysisRequest(
            **request_payload
        )
        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )

        calculator_warning = TargetAnalysisWarning(
            code=(
                TargetAnalysisWarningCode
                .HISTORICAL_RESULTS_NOT_GUARANTEED
            ),
            message=(
                "歷史結果不代表未來績效。"
            ),
            affected_fields=[],
        )
        duplicate_data_warning = (
            TargetAnalysisWarning(
                code=(
                    TargetAnalysisWarningCode
                    .HISTORICAL_RESULTS_NOT_GUARANTEED
                ),
                message=(
                    "資料載入器的重複警告。"
                ),
                affected_fields=[],
            )
        )
        incomplete_data_warning = (
            TargetAnalysisWarning(
                code=(
                    TargetAnalysisWarningCode
                    .INCOMPLETE_DIVIDEND_DATA
                ),
                message=(
                    "部分配息紀錄缺少殖利率。"
                ),
                affected_fields=[
                    "dividend_yield_pct",
                ],
            )
        )
        unavailable_field = (
            TargetAnalysisUnavailableField(
                field="dividend_yield_pct",
                reason=(
                    "部分配息紀錄缺少殖利率"
                ),
            )
        )

        calculator_result = run_target_analysis(
            parsed_request,
            context=context,
            gross_distribution_cash=Decimal(
                "1072"
            ),
            distribution_tax=Decimal("0"),
            supplementary_premium=Decimal("0"),
            other_distribution_costs=Decimal("0"),
            annual_gross_cash_rate_pct=Decimal(
                "3.019718"
            ),
            annual_price_return_pct=Decimal(
                "4"
            ),
        ).model_copy(
            update={
                "warnings": [
                    calculator_warning,
                ],
            },
        )

        loaded_data = TargetAnalysisData(
            monthly_income={
                "analysis_currency": "TWD",
                "has_mixed_currencies": False,
                "lookback_years": 3,
                "window_start_date": date(
                    2023,
                    1,
                    1,
                ),
                "as_of_date": date(
                    2025,
                    12,
                    31,
                ),
                "total_amount_per_unit": 3.216,
            },
            dividends=[],
            selected_performance={
                "period_code": "1Y",
                "return_pct": 4.0,
                "as_of_date": date(
                    2025,
                    12,
                    31,
                ),
            },
            warnings=[
                duplicate_data_warning,
                incomplete_data_warning,
            ],
            unavailable_fields=[
                unavailable_field,
            ],
        )

        mock_get_etf_by_code.return_value = {
            "code": "0056",
            "name": "元大高股息",
        }
        mock_load_target_analysis_data.return_value = (
            loaded_data
        )
        mock_calculate_target_analysis.return_value = (
            calculator_result
        )

        response = self.client.post(
            "/api/v1/etfs/0056/target-analysis",
            json=request_payload,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response_body = response.json()

        self.assertEqual(
            response_body["status"],
            TargetAnalysisStatus.PARTIAL.value,
        )
        self.assertEqual(
            [
                warning["code"]
                for warning in response_body["warnings"]
            ],
            [
                (
                    TargetAnalysisWarningCode
                    .HISTORICAL_RESULTS_NOT_GUARANTEED
                    .value
                ),
                (
                    TargetAnalysisWarningCode
                    .INCOMPLETE_DIVIDEND_DATA
                    .value
                ),
            ],
        )
        self.assertEqual(
            response_body["warnings"][0]["message"],
            calculator_warning.message,
        )
        self.assertEqual(
            response_body["unavailable_fields"],
            [
                unavailable_field.model_dump(
                    mode="json"
                ),
            ],
        )

        self.assertEqual(
            calculator_result.status,
            TargetAnalysisStatus.AVAILABLE,
        )
        self.assertEqual(
            calculator_result.warnings,
            [calculator_warning],
        )
        self.assertEqual(
            calculator_result.unavailable_fields,
            [],
        )

    @patch(
        "backend.app.api.routers.target_analysis."
        "calculate_target_analysis",
    )
    @patch(
        "backend.app.api.routers.target_analysis."
        "load_target_analysis_data",
    )
    @patch(
        "backend.app.api.routers.target_analysis."
        "get_etf_by_code",
    )
    def test_missing_income_and_performance_are_passed_as_none(
        self,
        mock_get_etf_by_code,
        mock_load_target_analysis_data,
        mock_calculate_target_analysis,
    ) -> None:
        """確認缺少配息總額與績效時仍可執行部分分析。"""

        request_payload = {
            **self._valid_request(),
            "unit_price": "30",
            "history_years": 5,
        }
        parsed_request = TargetAnalysisRequest(
            **request_payload
        )
        context = CalculationContext(
            mode=AnalysisMode.SCENARIO_ESTIMATE,
            currency="TWD",
            period_start=date(2021, 1, 1),
            period_end=date(2025, 12, 31),
        )
        expected_result = run_target_analysis(
            parsed_request,
            context=context,
            gross_distribution_cash=None,
            distribution_tax=None,
            supplementary_premium=None,
            other_distribution_costs=None,
            annual_gross_cash_rate_pct=None,
            annual_price_return_pct=None,
        )

        mock_get_etf_by_code.return_value = {
            "code": "0056",
            "name": "元大高股息",
        }
        mock_load_target_analysis_data.return_value = (
            TargetAnalysisData(
                monthly_income={
                    "analysis_currency": "TWD",
                    "has_mixed_currencies": False,
                    "lookback_years": 5,
                    "window_start_date": date(
                        2021,
                        1,
                        1,
                    ),
                    "as_of_date": date(
                        2025,
                        12,
                        31,
                    ),
                    "total_amount_per_unit": None,
                },
                dividends=[],
                selected_performance=None,
                warnings=[],
                unavailable_fields=[],
            )
        )
        mock_calculate_target_analysis.return_value = (
            expected_result
        )

        response = self.client.post(
            "/api/v1/etfs/0056/target-analysis",
            json=request_payload,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            expected_result.model_dump(
                mode="json"
            ),
        )
        mock_calculate_target_analysis.assert_called_once_with(
            parsed_request,
            context=context,
            gross_distribution_cash=None,
            distribution_tax=None,
            supplementary_premium=None,
            other_distribution_costs=None,
            annual_gross_cash_rate_pct=None,
            annual_price_return_pct=None,
        )
if __name__ == "__main__":
    unittest.main()
