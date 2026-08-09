"""M11-1 決策條件頁純顯示邏輯測試。"""

import unittest

from streamlit.testing.v1 import AppTest

from frontend.pages.decision_profile import build_holding_rows


class TestFrontendDecisionProfile(unittest.TestCase):
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

    def test_page_renders_native_forms_and_manual_boundary(self):
        app = AppTest.from_string(
            """
import frontend.pages.decision_profile as page

page.load_decision_profile = lambda api_base_url: {
    "profile_scope": "SINGLE_USER",
    "broker_connected": False,
    "conditions": None,
    "holdings": [],
}
page.render_decision_profile()
"""
        )
        app.run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.title[0].value, "我的條件與持有部位")
        captions = " ".join(item.value for item in app.caption)
        self.assertIn("不連接券商", captions)
        warnings = " ".join(item.value for item in app.warning)
        self.assertIn("公開部署前必須限制寫入存取", warnings)
        button_labels = [item.label for item in app.button]
        self.assertIn("儲存固定條件", button_labels)
        self.assertIn("新增或更新持有部位", button_labels)


if __name__ == "__main__":
    unittest.main()
