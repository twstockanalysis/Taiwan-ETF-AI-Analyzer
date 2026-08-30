"""ETF 比較頁純顯示邏輯測試。"""

import unittest
import inspect
from unittest.mock import patch

from frontend.pages.etf_comparison import (
    build_candidate_result_rows,
    build_completeness_rows,
    build_dividend_rows,
    build_monthly_coverage_rows,
    build_target_payment_months,
    build_performance_rows,
    format_percentage,
    parse_comparison_terms,
    render_code_form,
    render_etf_comparison,
    resolve_comparison_terms,
)


class TestFrontendETFComparison(
    unittest.TestCase
):
    """驗證比較表格與缺資料語意。"""

    def build_payload(self) -> dict:
        """建立兩檔 ETF 顯示資料。"""

        return {
            "periods": [
                "1M",
                "3M",
                "6M",
                "1Y",
            ],
            "items": [
                {
                    "etf": {
                        "code": "0050",
                        "name": "元大台灣50",
                    },
                    "performance_items": [
                        {
                            "period_code": "1M",
                            "return_pct": 5.0,
                            "as_of_date": "2026-07-30",
                        },
                    ],
                    "dividend": {
                        "event_count": 1,
                        "latest_event_date": "2026-07-15",
                        "latest_amount_per_unit": 0.7,
                        "currency": "TWD",
                    },
                    "actual_76w": {
                        "record_count": 1,
                        "latest_ratio_pct": 0.0,
                        "average_ratio_pct": 0.0,
                    },
                    "completeness": {
                        "available_section_count": 4,
                        "total_section_count": 5,
                        "score_pct": 80.0,
                        "missing_sections": [
                            "正式來源文件",
                        ],
                    },
                },
                {
                    "etf": {
                        "code": "0056",
                        "name": "元大高股息",
                    },
                    "performance_items": [],
                    "dividend": {
                        "event_count": 0,
                        "latest_event_date": None,
                        "latest_amount_per_unit": None,
                        "currency": None,
                    },
                    "actual_76w": {
                        "record_count": 0,
                        "latest_ratio_pct": None,
                        "average_ratio_pct": None,
                    },
                    "completeness": {
                        "available_section_count": 1,
                        "total_section_count": 5,
                        "score_pct": 20.0,
                        "missing_sections": [
                            "市價績效",
                            "配息歷史",
                            "正式 76W",
                            "正式來源文件",
                        ],
                    },
                },
            ],
        }

    def test_formal_zero_is_not_missing(
        self,
    ) -> None:
        """確認正式 0% 顯示為數值。"""

        self.assertEqual(
            format_percentage(0),
            "0.00%",
        )
        self.assertEqual(
            format_percentage(None),
            "尚未取得",
        )

    def test_missing_period_is_not_zero(
        self,
    ) -> None:
        """確認缺少績效顯示歷史資料不足。"""

        rows = build_performance_rows(
            self.build_payload()
        )

        self.assertEqual(
            rows[0]["0056"],
            "歷史資料不足",
        )
        self.assertIn(
            "+5.00%",
            rows[0]["0050"],
        )

    def test_dividend_and_completeness_rows(
        self,
    ) -> None:
        """確認配息與完整度說明可並列。"""

        payload = self.build_payload()
        dividend_rows = build_dividend_rows(
            payload
        )
        completeness_rows = (
            build_completeness_rows(
                payload
            )
        )

        self.assertEqual(
            dividend_rows[0][
                "最新 76W 比例"
            ],
            "0.00%",
        )
        self.assertEqual(
            dividend_rows[1][
                "最新 76W 比例"
            ],
            "尚未取得",
        )
        self.assertIn(
            "市價績效",
            completeness_rows[1][
                "缺少區塊"
            ],
        )

    def test_monthly_coverage_preserves_missing_and_formal_months(self):
        rows = build_monthly_coverage_rows(
            {
                "base_payment_months": [1],
                "combined_payment_months": [1, 2],
            }
        )
        self.assertEqual(rows[0]["基準 ETF"], "有歷史付款")
        self.assertEqual(rows[1]["基準 ETF"], "未覆蓋")
        self.assertEqual(rows[1]["組合情境"], "有歷史付款")
        missing = build_monthly_coverage_rows(
            {"base_payment_months": None, "combined_payment_months": None}
        )
        self.assertEqual(missing[0]["基準 ETF"], "資料不足")

    def test_candidate_rows_show_classification_and_reasons(self):
        rows = build_candidate_result_rows(
            [
                {
                    "etf_code": "00878",
                    "name": "國泰永續高股息",
                    "is_active": False,
                    "is_bond": False,
                    "supported_gap_months": [2, 5],
                    "completeness_pct": 100,
                    "distribution_stability_pct": 75,
                    "data_is_fresh": True,
                    "annual_after_tax_cash_rate_pct": 0,
                    "estimated_after_tax_total_return_pct": -1,
                    "downside_return_pct": -5,
                    "holding_overlap_pct": None,
                    "reasons": [{"message": "總報酬未達門檻。"}],
                }
            ]
        )
        self.assertEqual(rows[0]["估算稅後現金率"], "0.00%")
        self.assertEqual(rows[0]["自動持股重疊"], "尚未取得")
        self.assertIn("總報酬", rows[0]["理由"])

    def test_custom_target_month_presets(self) -> None:
        self.assertEqual(build_target_payment_months("全年每月"), list(range(1, 13)))
        self.assertEqual(build_target_payment_months("單月", anchor_month=6), [6])
        self.assertEqual(
            build_target_payment_months("隔月", anchor_month=2), [2, 4, 6, 8, 10, 12]
        )
        self.assertEqual(
            build_target_payment_months("每季", anchor_month=3), [3, 6, 9, 12]
        )
        self.assertEqual(
            build_target_payment_months("任意月份", custom_months=[12, 3, 3]),
            [3, 12],
        )

    def test_coverage_marks_non_target_months(self) -> None:
        rows = build_monthly_coverage_rows({
            "base_payment_months": [1, 4],
            "target_payment_months": [1, 2],
            "combined_payment_months": [1, 2],
        })
        self.assertEqual(rows[1]["目標"], "是")
        self.assertEqual(rows[2]["目標"], "否")
        self.assertEqual(rows[2]["組合情境"], "不列入目標")

    def test_public_comparison_hides_operational_completeness(self) -> None:
        """確認公開比較頁不渲染管理用途的完整度區塊。"""

        source = inspect.getsource(render_etf_comparison)
        self.assertNotIn('st.subheader("資料完整度")', source)
        self.assertNotIn("build_completeness_rows(", source)

    def test_comparison_action_uses_beginner_copy(self) -> None:
        """確認比較提示緊接在主要動作下方。"""

        source = inspect.getsource(render_code_form)
        self.assertIn('"開始比較"', source)
        self.assertIn(
            '"請輸入至少2檔才能比較，最多同時比較4檔"',
            source,
        )
        self.assertGreater(
            source.index(
                '"請輸入至少2檔才能比較，最多同時比較4檔"'
            ),
            source.index('"開始比較"'),
        )
        self.assertIn('placeholder="輸入ETF代號或名稱"', source)
        self.assertNotIn("請選擇至少", source)

    def test_comparison_terms_accept_full_width_commas_and_lines(self) -> None:
        """比較輸入支援常見的中文逗號與換行。"""

        self.assertEqual(
            parse_comparison_terms("0050，元大高股息\n00878"),
            ["0050", "元大高股息", "00878"],
        )

    @patch("frontend.pages.etf_comparison.fetch_etfs")
    def test_comparison_terms_resolve_code_name_and_unique_keyword(
        self,
        mock_fetch_etfs,
    ) -> None:
        """代號、完整名稱與唯一名稱關鍵字皆可解析。"""

        catalog = {
            "0050": [{"code": "0050", "name": "元大台灣50"}],
            "元大高股息": [{"code": "0056", "name": "元大高股息"}],
            "永續高股息": [{"code": "00878", "name": "國泰永續高股息"}],
        }

        def fake_fetch_etfs(**kwargs):
            items = catalog[kwargs["keyword"]]
            return {
                "items": items,
                "total": len(items),
                "limit": 100,
                "offset": 0,
            }

        mock_fetch_etfs.side_effect = fake_fetch_etfs

        codes, unresolved, ambiguous = resolve_comparison_terms(
            "http://api",
            ["0050", "元大高股息", "永續高股息"],
        )

        self.assertEqual(codes, ("0050", "0056", "00878"))
        self.assertEqual(unresolved, [])
        self.assertEqual(ambiguous, [])

    @patch("frontend.pages.etf_comparison.fetch_etfs")
    def test_comparison_terms_do_not_guess_ambiguous_names(
        self,
        mock_fetch_etfs,
    ) -> None:
        """多筆名稱關鍵字不應任意挑選其中一檔。"""

        mock_fetch_etfs.return_value = {
            "items": [
                {"code": "0050", "name": "元大台灣50"},
                {"code": "006203", "name": "元大MSCI台灣"},
            ],
            "total": 2,
            "limit": 100,
            "offset": 0,
        }

        codes, unresolved, ambiguous = resolve_comparison_terms(
            "http://api",
            ["元大"],
        )

        self.assertEqual(codes, ())
        self.assertEqual(unresolved, [])
        self.assertEqual(ambiguous, ["元大"])


if __name__ == "__main__":
    unittest.main()
