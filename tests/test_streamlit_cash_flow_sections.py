"""直接驗證 M11-5 現金流相關 Streamlit 結果區塊。"""

import unittest

from streamlit.testing.v1 import AppTest


TAX_SCRIPT = r'''
from frontend.pages.etf_detail import _render_tax_reinvestment_result

scenario = {
    "usable_cash": 1000,
    "reinvested_cash": 500,
    "ending_units": 1100,
    "ending_value": 35000,
    "modeled_tax_cost": 100,
    "after_tax_total_return_pct": -1,
    "total_return_check_passed": False,
}
_render_tax_reinvestment_result({
    "status": "AVAILABLE",
    "historical_facts": {
        "component_source_event_id": "evt-1",
        "component_source_date": "2026-06-01",
        "annual_gross_distribution_rate_pct": 5,
        "price_return_period_code": "1Y",
        "annual_price_return_pct": -3,
        "actual_component_mix": None,
    },
    "calculation": {
        "currency": "TWD",
        "rule_version": "TW-INDIVIDUAL-2026.1",
        "rule_effective_date": "2026-01-01",
        "issues": [],
        "scenarios": [
            {**scenario, "policy": "NO_REINVESTMENT"},
            {**scenario, "policy": "EXCESS_ONLY"},
            {**scenario, "policy": "CUSTOM_PERCENTAGE"},
            {**scenario, "policy": "FULL_REINVESTMENT"},
        ],
    },
})
'''


MONTHLY_SCRIPT = r'''
from frontend.pages.etf_comparison import render_monthly_combination_result

candidate = {
    "etf_code": "00878", "name": "國泰永續高股息",
    "is_active": False, "is_bond": False,
    "supported_gap_months": [2, 5], "completeness_pct": 100,
    "distribution_stability_pct": 90, "data_is_fresh": True,
    "annual_after_tax_cash_rate_pct": 4,
    "estimated_after_tax_total_return_pct": 3,
    "downside_return_pct": -8, "holding_overlap_pct": None,
    "reasons": [{"message": "補足 2月、5月"}],
}
render_monthly_combination_result({
    "cash_deduction_rate_pct": 5,
    "historical_facts": {"lookback_years": 3, "as_of_date": "2026-08-12"},
    "calculation": {
        "status": "AVAILABLE", "base_etf_code": "0056",
        "base_etf_name": "元大高股息", "base_payment_months": [1, 4],
        "combined_payment_months": [1, 2, 4, 5],
        "selected_candidates": [candidate], "rejected_candidates": [],
        "estimate_label": "歷史情境估算，不保證未來",
    },
})
'''


WARNING_SCRIPT = r'''
from frontend.pages.etf_detail import _render_target_analysis_result

_render_target_analysis_result({
    "cash_flow": {
        "required_capital": 1000000, "funding_shortfall": 500000,
        "annual_after_tax_target": 36000, "target_coverage_pct": 50,
    },
    "scenario_estimate": {"after_tax_total_return_pct": -2},
    "monthly_cash_flow": [{
        "month": month, "event_count": 0, "observed_year_count": 0,
        "annualized_gross_cash": None, "annualized_after_tax_cash": None,
        "latest_payment_date": None,
    } for month in range(1, 13)],
    "warnings": [{
        "code": "PERSISTENT_PRICE_DECLINE",
        "message": "最近三個月末收盤價連續下跌。",
        "as_of_date": "2026-08-07", "source_id": "twse_stock_day",
        "evidence": {"decline_pct": -12, "threshold_pct": -10},
    }],
    "unavailable_fields": [],
})
'''


class TestStreamlitCashFlowSections(unittest.TestCase):
    def test_tax_section_renders_all_four_policies_and_risk_gate(self) -> None:
        app = AppTest.from_string(TAX_SCRIPT).run()
        self.assertEqual(len(app.exception), 0)
        rendered = "\n".join(str(item.value) for item in app.table)
        for label in (
            "不再投入", "僅投入超過目標的現金",
            "自訂比例再投入", "全部再投入",
        ):
            self.assertIn(label, rendered)
        self.assertTrue(any("未通過總報酬檢查" in item.value for item in app.error))

    def test_monthly_combination_renders_anchor_months_and_reason(self) -> None:
        app = AppTest.from_string(MONTHLY_SCRIPT).run()
        self.assertEqual(len(app.exception), 0)
        text = "\n".join(
            str(item.value) for item in [*app.markdown, *app.caption, *app.table]
        )
        self.assertIn("基準 ETF：0056 元大高股息", text)
        self.assertIn("00878 國泰永續高股息", text)
        self.assertIn("補足 2月、5月", text)
        self.assertIn("稅後現金扣除率假設：5.00%", text)

    def test_principal_warning_renders_date_source_and_evidence(self) -> None:
        app = AppTest.from_string(WARNING_SCRIPT).run()
        self.assertEqual(len(app.exception), 0)
        captions = "\n".join(item.value for item in app.caption)
        self.assertIn("資料基準日 2026-08-07", captions)
        self.assertIn("來源 twse_stock_day", captions)
        self.assertIn("decline_pct=-12", captions)


if __name__ == "__main__":
    unittest.main()
