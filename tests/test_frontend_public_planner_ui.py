"""V4-3 公開股利試算頁資訊架構測試。"""

import unittest
from inspect import getsource

from streamlit.testing.v1 import AppTest

from frontend.pages.public_planner import (
    DEFAULT_HISTORY_YEARS,
    MONTH_OPTIONS,
    render_allocation_results,
    render_public_planner,
)
from frontend.ui.theme import GLOBAL_STYLES


PLANNER_PAGE_SCRIPT = """
from frontend.pages.public_planner import render_public_planner

render_public_planner()
"""

PLANNER_API_ERROR_SCRIPT = """
from unittest.mock import patch

from frontend.api.errors import APIClientError
from frontend.pages.public_planner import render_public_planner

with patch(
    "frontend.pages.public_planner.fetch_portfolio_projections",
    side_effect=APIClientError("offline"),
):
    render_public_planner()
"""

ALLOCATION_RESULT_SCRIPT = """
from frontend.pages.public_planner import render_allocation_results

render_allocation_results(
    {
        "estimate_label": "依歷史資料建立的配置情境。",
        "plans": [
            {
                "strategy": "RECOMMENDED",
                "label": "推薦配置",
                "simple_explanation": "依現金流缺口與所需資金產生。",
                "result": {
                    "status": "PARTIAL",
                    "optimality": "BOUNDED_BEST_EFFORT",
                    "snapshot_id": "sha256:test",
                    "total_required_additional_capital": "3500",
                    "additions": [
                        {
                            "etf_code": "0056",
                            "name": "元大高股息",
                            "additional_shares": 100,
                            "required_capital": "3500",
                            "supported_target_months": [1, 7],
                            "reasons": ["用來縮小 1 月與 7 月的現金流缺口。"],
                            "risks": ["部分歷史證據仍不足。"],
                            "historical_quality_grade": {
                                "status": "UNRATED",
                                "grade": None,
                                "explanation": "市場校準尚未達到發布門檻。",
                                "strengths": [],
                                "unavailable_evidence": ["可信樣本不足。"],
                            },
                        }
                    ],
                    "monthly_results": [
                        {
                            "month": 1,
                            "current_after_tax_cash": "0",
                            "added_after_tax_cash": "100",
                            "modeled_after_tax_cash": "100",
                            "target_after_tax_cash": "100",
                            "shortfall": "0",
                        },
                        {
                            "month": 7,
                            "current_after_tax_cash": "0",
                            "added_after_tax_cash": "50",
                            "modeled_after_tax_cash": "50",
                            "target_after_tax_cash": "100",
                            "shortfall": "50",
                        },
                    ],
                    "resulting_holdings": [],
                    "issues": [{"message": "7 月仍有缺口。"}],
                    "assumptions": {"transaction_cost_note": "交易成本固定以 0 元試算。"},
                },
            }
        ],
        "strategy_issues": [{"message": "成分股資料不足，暫無其他方案。"}],
        "excluded_candidates": [
            {
                "etf_code": "00999",
                "name": "測試 ETF",
                "reasons": [{"message": "總報酬資料不足。"}],
            }
        ],
    }
)
"""


class TestFrontendPublicPlannerUI(unittest.TestCase):
    def test_allocation_result_separates_owner_fit_from_etf_quality(self) -> None:
        app = AppTest.from_string(ALLOCATION_RESULT_SCRIPT, default_timeout=10)
        app.run()

        self.assertEqual(len(app.exception), 0)
        page_text = "\n".join(
            [item.value for item in app.markdown]
            + [item.value for item in app.caption]
        )
        self.assertIn("主人目標適配只針對本次輸入", page_text)
        self.assertIn("這是 ETF 歷史品質，不代表一定適合每位主人", page_text)
        self.assertIn("為什麼放進這個配置", page_text)
        self.assertNotIn("quality_score", page_text)
        self.assertNotIn("confidence", page_text)

        metric_labels = [item.label for item in app.metric]
        self.assertIn("新增所需資金", metric_labels)
        self.assertIn("達標月份", metric_labels)
        self.assertIn("尚缺總額", metric_labels)
        self.assertIn("增加股數", metric_labels)

        source = getsource(render_allocation_results)
        self.assertIn("查看配置後持股與計算假設", source)
        self.assertIn("為什麼沒有更多不同方案", source)
        self.assertIn("查看未納入的 ETF", source)

    def test_primary_inputs_follow_beginner_order(self) -> None:
        app = AppTest.from_string(PLANNER_PAGE_SCRIPT, default_timeout=10)
        app.run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "股利試算")
        self.assertEqual(
            app.caption[0].value,
            "先選領息月份，再設定目標；不用自己先挑候選 ETF。",
        )

        number_labels = [item.label for item in app.number_input]
        self.assertEqual(
            number_labels[:2],
            [
                "每個目標月想領多少股利（TWD）",
                "想持有年限",
            ],
        )
        self.assertEqual(app.number_input[0].value, 3000)
        self.assertEqual(app.number_input[1].value, 10)
        monthly_button = next(item for item in app.button if item.label == "每月")
        self.assertEqual(monthly_button.proto.type, "primary")

        source = getsource(render_public_planner)
        self.assertEqual(MONTH_OPTIONS, list(range(1, 13)))
        self.assertEqual(DEFAULT_HISTORY_YEARS, 3)
        self.assertEqual(
            [item.value for item in app.subheader[:5]],
            [
                "1. 想在哪些月份領股利",
                "2. 每個目標月想領多少股利（TWD）",
                "3. 想持有年限",
                "4. 庫存 ETF 持股（可留空）",
                "5. 股息再投入與否",
            ],
        )
        self.assertIn('st.pills(', source)
        self.assertIn('selection_mode="multi"', source)
        self.assertIn('key="public-planner-guided-form"', source)
        self.assertIn("GoodCatState.ATTENTIVE", source)
        self.assertIn("GoodCatState.WORKING", source)
        self.assertIn("GoodCatState.CAUTION", source)
        self.assertIn("查看歷史績效與長期情境", source)
        self.assertIn("年稅務與再投入試算", source)
        self.assertNotIn('st.form(', source)
        self.assertNotIn('st.form_submit_button(', source)
        self.assertIn('num_rows="fixed"', source)
        self.assertIn('width="content"', source)
        self.assertIn('CheckboxColumn(', source)
        self.assertIn('st.expander("稅務假設（可調整）")', source)
        self.assertNotIn("稅務與再投入假設", source)
        self.assertIn(
            '.st-key-public-planner-holdings [data-testid="stElementToolbar"]',
            GLOBAL_STYLES,
        )
        self.assertIn('button[aria-label*="column menu" i]', GLOBAL_STYLES)
        self.assertGreater(source.index('"新增持股"'), source.index("st.data_editor("))

        captions = [item.value for item in app.caption]
        self.assertIn(
            "請輸入代號＋股數，價格自動擷取最新收盤價，非即時報價；"
            "若在盤中，則為前一日收盤價。",
            captions,
        )
        self.assertIn(
            "不需登入，輸入只用於本次試算；結果不是下單指示，也不保證未來配息或報酬。",
            captions,
        )

    def test_odd_month_preset_updates_month_pills(self) -> None:
        app = AppTest.from_string(PLANNER_PAGE_SCRIPT, default_timeout=10)
        app.run()

        odd_button = next(item for item in app.button if item.label == "單數月")
        odd_button.click().run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.pills[0].value, [1, 3, 5, 7, 9, 11])
        monthly_button = next(item for item in app.button if item.label == "每月")
        odd_button = next(item for item in app.button if item.label == "單數月")
        self.assertEqual(monthly_button.proto.type, "secondary")
        self.assertEqual(odd_button.proto.type, "primary")

    def test_delete_action_is_hidden_until_a_holding_is_selected(self) -> None:
        app = AppTest.from_string(PLANNER_PAGE_SCRIPT, default_timeout=10)
        app.run()

        button_labels = [item.label for item in app.button]
        self.assertIn("新增持股", button_labels)
        self.assertNotIn("刪除已選取（1）", button_labels)

    def test_technical_allocation_inputs_are_not_exposed(self) -> None:
        app = AppTest.from_string(PLANNER_PAGE_SCRIPT, default_timeout=10)
        app.run()

        labels = [item.label for item in app.number_input]
        self.assertNotIn("歷史配息年數", labels)
        self.assertNotIn("配置階段現金扣除率（%）", labels)
        self.assertEqual(len(app.multiselect), 0)

        page_text = "\n".join(
            [item.value for item in app.caption]
            + [item.value for item in app.markdown]
        )
        self.assertIn("直接算出可能的所得稅與二代健保金額", page_text)

    def test_service_error_keeps_inputs_and_uses_plain_language_caution(self) -> None:
        app = AppTest.from_string(PLANNER_API_ERROR_SCRIPT, default_timeout=10)
        app.run()

        submit = next(
            item for item in app.button if item.label == "讓股利喵產生配置"
        )
        submit.click().run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.number_input[0].value, 3000)
        self.assertIn(
            "暫時無法完成股利試算，請確認服務已啟動後再試一次。",
            [item.value for item in app.error],
        )
        page_text = "\n".join(item.value for item in app.markdown)
        self.assertIn("主人剛才的輸入仍留在畫面上", page_text)
        self.assertNotIn("offline", page_text)


if __name__ == "__main__":
    unittest.main()
