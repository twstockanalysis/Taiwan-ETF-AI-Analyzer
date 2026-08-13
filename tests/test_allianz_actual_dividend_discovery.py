"""安聯投信官方產品公告探索測試。"""

import unittest

from backend.app.data_sources.allianz_actual_dividend_discovery import (
    discover_allianz_dividend_documents,
    parse_allianz_product_announcements,
)


def _tile(*, href: str, title: str) -> str:
    return f'''<div class="tile-article"><h3>{title}</h3>
    <a href="{href}" aria-label="{title}">了解更多</a></div>'''


class TestAllianzActualDividendDiscovery(unittest.TestCase):
    def test_accepts_target_actual_distribution_article(self) -> None:
        result = parse_allianz_product_announcements(
            etf_code="00984A",
            html_text=_tile(
                href="/zh-tw/announcement/product-announcement/2026-10-15-1",
                title="00984A 2026/10/15 實際配發收益分配公告",
            ),
        )

        self.assertEqual(len(result.candidates), 1)
        candidate = result.candidates[0]
        self.assertEqual(candidate.etf_code, "00984A")
        self.assertEqual(candidate.declared_date.isoformat(), "2026-10-15")
        self.assertEqual(candidate.information_basis, "UNKNOWN")
        self.assertTrue(candidate.document_url.startswith("https://tw.allianzgi.com/"))

    def test_rejects_estimated_target_article(self) -> None:
        result = parse_allianz_product_announcements(
            etf_code="00984A",
            html_text=_tile(
                href="/zh-tw/announcement/product-announcement/estimated",
                title="00984A 收益分配期前預估公告",
            ),
        )

        self.assertEqual(result.candidates, ())
        self.assertEqual(len(result.rejections), 1)

    def test_ignores_initial_market_and_other_etf_articles(self) -> None:
        html = _tile(
            href="/zh-tw/announcement/product-announcement/initial",
            title="00984A 結束初級市場配售公告",
        ) + _tile(
            href="/zh-tw/announcement/product-announcement/other",
            title="00999 2026/10/15 實際配發收益分配公告",
        )

        result = parse_allianz_product_announcements(
            etf_code="00984A", html_text=html,
        )

        self.assertEqual(result.candidates, ())
        self.assertEqual(result.rejections, ())

    def test_network_access_requires_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            discover_allianz_dividend_documents(etf_code="00984A")


if __name__ == "__main__":
    unittest.main()
