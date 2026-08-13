"""全部待接入投信的官方公告入口測試。"""

import unittest
from urllib.parse import urlsplit

from backend.app.data_sources.issuer_dividend_landing_pages import (
    ISSUER_DIVIDEND_LANDING_PAGES,
    get_issuer_dividend_landing_page,
)


class TestIssuerDividendLandingPages(unittest.TestCase):
    def test_all_remaining_issuers_have_https_official_entrypoints(self) -> None:
        self.assertEqual(len(ISSUER_DIVIDEND_LANDING_PAGES), 17)
        for issuer_key, page in ISSUER_DIVIDEND_LANDING_PAGES.items():
            with self.subTest(issuer_key=issuer_key):
                parsed = urlsplit(page.url)
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.hostname, page.official_domains)
                self.assertEqual(page.issuer_key, issuer_key)
                self.assertTrue(page.page_kind)

    def test_lookup_normalizes_issuer_key(self) -> None:
        self.assertEqual(
            get_issuer_dividend_landing_page(" YUANTA ").issuer_key,
            "yuanta",
        )

    def test_unknown_issuer_is_rejected(self) -> None:
        with self.assertRaises(KeyError):
            get_issuer_dividend_landing_page("unknown")


if __name__ == "__main__":
    unittest.main()
