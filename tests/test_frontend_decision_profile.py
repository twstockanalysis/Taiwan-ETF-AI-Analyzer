"""M11-1 決策條件頁純顯示邏輯測試。"""

import unittest

from streamlit.testing.v1 import AppTest

from frontend.pages.decision_profile import (
    build_analysis_holding_rows,
    build_candidate_comparison_rows,
    build_decision_record_rows,
    build_holding_rows,
)


class TestFrontendDecisionProfile(unittest.TestCase):
    def test_decision_record_rows_use_human_readable_outcome(self):
        rows = build_decision_record_rows(
            [{
                "id": 3,
                "created_at": "2026-08-10T12:00:00",
                "candidate_etf_code": "00878",
                "candidate_name": "國泰永續高股息",
                "analysis_status": "PARTIAL",
                "outcome": "INELIGIBLE",
            }]
        )
        self.assertEqual(rows[0]["紀錄"], "#3")
        self.assertEqual(rows[0]["資格結果"], "未通過目前門檻")

    def test_holding_rows_calculate_reference_value(self):
        rows = build_holding_rows(
            {
                "holdings": [
                    {
                        "etf_code": "0056",
                        "name": "元大高股息",
                        "is_active": False,
                        "is_bond": False,
                        "held_units": 1000,
                        "unit_price": "35.5",
                        "price_as_of_date": None,
                    }
                ]
            }
        )
        self.assertEqual(rows[0]["參考部位價值"], "35,500.00 TWD")
        self.assertEqual(rows[0]["價格日期"], "未提供")
        self.assertEqual(rows[0]["管理方式"], "被動式")

    def test_missing_price_is_not_zero(self):
        rows = build_holding_rows(
            {
                "holdings": [
                    {
                        "etf_code": "0056",
                        "name": "元大高股息",
                        "is_active": False,
                        "is_bond": False,
                        "held_units": 1000,
                        "unit_price": None,
                        "price_as_of_date": None,
                    }
                ]
            }
        )
        self.assertEqual(rows[0]["參考單價"], "尚未取得")
        self.assertEqual(rows[0]["參考部位價值"], "無法計算")

    def test_analysis_rows_keep_missing_history_distinct_from_zero(self):
        rows = build_analysis_holding_rows(
            {
                "holdings": [
                    {
                        "etf_code": "0056",
                        "name": "元大高股息",
                        "current_value": "35500",
                        "annual_gross_distribution_cash": None,
                        "price_return_period_code": None,
                        "annualized_price_return_pct": None,
                    }
                ]
            }
        )
        self.assertEqual(rows[0]["年均稅前配息現金"], "無法計算")
        self.assertEqual(rows[0]["價格報酬期間"], "無資料")

    def test_candidate_comparison_keeps_missing_values_explicit(self):
        rows = build_candidate_comparison_rows(
            {
                "total_value_before": "30000",
                "total_value_after": "32000",
                "annual_after_tax_cash_before": None,
                "annual_after_tax_cash_after": None,
            }
        )
        self.assertEqual(rows[0]["目前持倉"], "30,000.00 TWD")
        self.assertEqual(rows[0]["加入候選後"], "32,000.00 TWD")
        self.assertEqual(rows[1]["目前持倉"], "無法計算")

    def test_page_renders_native_forms_and_manual_boundary(self):
        app = AppTest.from_string(
            """
import frontend.pages.decision_profile as page

page.load_decision_profile = lambda api_base_url: {
    "profile_scope": "SINGLE_USER",
    "broker_connected": False,
    "conditions": None,
    "holdings": [{
        "etf_code": "0056",
        "name": "元大高股息",
        "is_active": False,
        "is_bond": False,
        "held_units": 1000,
        "unit_price": "35.5",
        "price_as_of_date": None,
    }],
}
page.load_decision_records = lambda api_base_url: []
page.render_decision_profile()
"""
        )
        app.run(timeout=10)
        self.assertEqual(app.exception, [])
        self.assertEqual(app.title[0].value, "我的條件與持有部位")
        captions = " ".join(item.value for item in app.caption)
        self.assertIn("不連接券商", captions)
        warnings = " ".join(item.value for item in app.warning)
        self.assertIn("公開部署前必須限制寫入存取", warnings)
        button_labels = [item.label for item in app.button]
        self.assertIn("儲存固定條件", button_labels)
        self.assertIn("新增或更新持有部位", button_labels)
        self.assertIn("分析目前持倉", button_labels)
        self.assertIn("比較候選加入前後", button_labels)

    def test_analysis_action_renders_portfolio_metrics(self):
        app = AppTest.from_string(
            '''
import frontend.pages.decision_profile as page

page.load_decision_profile = lambda api_base_url: {
    "profile_scope": "SINGLE_USER",
    "broker_connected": False,
    "conditions": None,
    "holdings": [{
        "etf_code": "0056", "name": "元大高股息",
        "is_active": False, "is_bond": False,
        "held_units": 1000, "unit_price": "35.5",
        "price_as_of_date": None,
    }],
}
page.load_current_holding_analysis = lambda api_base_url: {
    "status": "AVAILABLE", "analysis_date": "2026-08-09",
    "total_current_value": "35500",
    "unavailable_fields": [],
    "holdings": [{
        "etf_code": "0056", "name": "元大高股息",
        "current_value": "35500",
        "annual_gross_distribution_cash": "2400",
        "price_return_period_code": "3Y",
        "annualized_price_return_pct": "5",
        "warnings": [],
    }],
    "portfolio_analysis": {
        "cash_flow": {
            "gross_distribution_cash": "2400",
            "after_tax_usable_cash": "2160",
            "target_coverage_pct": "60",
        },
        "scenario_estimate": {"projection_years": 10},
    },
}
page.load_decision_records = lambda api_base_url: []
page.render_decision_profile()
'''
        )
        app.run(timeout=10)
        next(
            button for button in app.button
            if button.label == "分析目前持倉"
        ).click().run(timeout=10)
        self.assertEqual(app.exception, [])
        metric_values = {item.label: item.value for item in app.metric}
        self.assertEqual(metric_values["目前部位總值"], "35,500.00 TWD")
        self.assertEqual(metric_values["年度目標覆蓋率"], "60.00%")

    def test_candidate_result_renders_deltas_and_reasons(self):
        app = AppTest.from_string(
            '''
from frontend.pages.decision_profile import render_candidate_holding_analysis_result

render_candidate_holding_analysis_result({
    "status": "AVAILABLE",
    "estimate_label": "候選 ETF 加碼情境，非投資建議或保證",
    "unavailable_fields": [],
    "comparison": {
        "additional_capital": "2000",
        "total_value_before": "30000",
        "total_value_after": "32000",
        "annual_after_tax_cash_before": "1000",
        "annual_after_tax_cash_after": "1200",
        "annual_after_tax_cash_delta": "200",
        "target_coverage_pct_before": "20",
        "target_coverage_pct_after": "24",
        "target_coverage_pct_delta": "4",
        "funding_shortfall_before": "10000",
        "funding_shortfall_after": "8000",
        "funding_shortfall_reduction": "2000",
        "after_tax_total_return_pct_before": "5",
        "after_tax_total_return_pct_after": "5.5",
    },
    "eligibility": {
        "selected_candidates": [{
            "reasons": [{
                "code": "PASSES_ELIGIBILITY",
                "message": "通過資料品質與風險門檻。",
            }]
        }],
        "rejected_candidates": [],
    },
})
'''
        )
        app.run(timeout=10)
        self.assertEqual(app.exception, [])
        metric_values = {item.label: item.value for item in app.metric}
        self.assertEqual(metric_values["目標覆蓋率變化"], "4.00%")
        successes = " ".join(item.value for item in app.success)
        self.assertIn("通過資料品質與風險門檻", successes)

    def test_saved_record_can_prepare_excel_download(self):
        app = AppTest.from_string(
            '''
import frontend.pages.decision_profile as page

page.load_decision_profile = lambda api_base_url: {
    "profile_scope": "SINGLE_USER",
    "broker_connected": False,
    "conditions": None,
    "holdings": [{
        "etf_code": "0056", "name": "元大高股息",
        "is_active": False, "is_bond": False,
        "held_units": 1000, "unit_price": "30",
        "price_as_of_date": None,
    }],
}
page.load_decision_records = lambda api_base_url: [{
    "id": 1,
    "record_type": "CANDIDATE_HOLDING_ANALYSIS",
    "candidate_etf_code": "00878",
    "candidate_name": "國泰永續高股息",
    "analysis_status": "PARTIAL",
    "outcome": "INELIGIBLE",
    "created_at": "2026-08-10T12:00:00",
}]
page.fetch_decision_record_export = lambda api_base_url, record_id: b"xlsx"
page.render_decision_profile()
'''
        )
        app.run(timeout=10)
        next(
            button for button in app.button if button.label == "準備 Excel"
        ).click().run(timeout=10)
        self.assertEqual(app.exception, [])
        download_buttons = app.get("download_button")
        self.assertEqual(download_buttons[0].label, "下載 Excel")


if __name__ == "__main__":
    unittest.main()
