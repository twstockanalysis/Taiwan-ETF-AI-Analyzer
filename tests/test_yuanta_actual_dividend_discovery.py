"""元大投信官方 ETF 公告探索測試。"""

import unittest

from backend.app.data_sources.yuanta_actual_dividend_discovery import (
    discover_yuanta_dividend_documents,
    parse_yuanta_announcements,
)


def _link(identifier: str, title: str) -> str:
    return f'<a href="/news/announcement/{identifier}">{title}</a>'


class TestYuantaActualDividendDiscovery(unittest.TestCase):
    def test_accepts_target_actual_amount_announcement(self) -> None:
        result = parse_yuanta_announcements(
            etf_code="0056",
            html_text=_link("actual", "2026/08/07 元大高股息(0056)每受益權單位實際配發金額"),
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].declared_date.isoformat(), "2026-08-07")
        self.assertEqual(result.candidates[0].information_basis, "UNKNOWN")

    def test_rejects_evaluation_and_estimated_announcements(self) -> None:
        result = parse_yuanta_announcements(
            etf_code="0056", html_text=_link("estimate", "0056 收益分配評價結果預估公告"),
        )
        self.assertEqual(result.candidates, ())
        self.assertEqual(len(result.rejections), 1)

    def test_ignores_other_etf(self) -> None:
        result = parse_yuanta_announcements(
            etf_code="0056", html_text=_link("other", "00940 每受益權單位實際配發金額"),
        )
        self.assertEqual(result.candidates, ())

    def test_uses_verified_name_alias_when_title_omits_code(self) -> None:
        result = parse_yuanta_announcements(
            etf_code="00940",
            html_text=_link(
                "actual-00940",
                "2026/08/07 公告元大臺灣價值高息ETF每受益權單位實際配發金額",
            ),
        )
        self.assertEqual(len(result.candidates), 1)

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            discover_yuanta_dividend_documents(etf_code="0056")


if __name__ == "__main__":
    unittest.main()
