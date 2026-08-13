"""投信官方公告入口共用解析器測試。"""

import unittest
from unittest.mock import Mock, patch

from backend.app.data_sources.issuer_landing_page_discovery import (
    discover_issuer_landing_page_documents,
    parse_issuer_landing_page,
)


class TestIssuerLandingPageDiscovery(unittest.TestCase):
    def test_official_actual_link_is_unknown_candidate(self) -> None:
        result = parse_issuer_landing_page(
            issuer_key="yuanta",
            etf_code="0050",
            html_text="""
            <a href="/News/123">2026/07/17 0050 收益分配實際配發金額</a>
            """,
        )
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].information_basis, "UNKNOWN")
        self.assertEqual(
            result.candidates[0].declared_date.isoformat(), "2026-07-17"
        )

    def test_estimated_and_external_links_are_rejected(self) -> None:
        result = parse_issuer_landing_page(
            issuer_key="yuanta",
            etf_code="0050",
            html_text="""
            <a href="/News/1">0050 收益分配期前公告</a>
            <a href="https://example.com/a.pdf">0050 收益分配公告</a>
            """,
        )
        self.assertEqual(result.candidates, ())
        self.assertEqual(len(result.rejections), 2)

    def test_other_etf_and_non_dividend_links_are_ignored(self) -> None:
        result = parse_issuer_landing_page(
            issuer_key="yuanta",
            etf_code="0050",
            html_text="""
            <a href="/News/1">0056 收益分配公告</a>
            <a href="/News/2">0050 公開說明書公告</a>
            """,
        )
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.rejections, ())

    def test_official_onclick_document_url_is_discovered(self) -> None:
        result = parse_issuer_landing_page(
            issuer_key="franklin",
            etf_code="00961",
            html_text="""
            <a href="#" onclick="openUrl('id',
              'https://www.ftft.com.tw/Content/Download/pdf/actual.pdf');">
              【00961】收益分配公告-金額公告 2026/07/14
            </a>
            """,
        )

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(
            result.candidates[0].document_url,
            "https://www.ftft.com.tw/Content/Download/pdf/actual.pdf",
        )
        self.assertEqual(result.candidates[0].content_type, "application/pdf")

    def test_invalid_code_and_limit_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_issuer_landing_page(
                issuer_key="yuanta", etf_code="../0050", html_text="x"
            )
        with self.assertRaises(ValueError):
            parse_issuer_landing_page(
                issuer_key="yuanta", etf_code="0050", html_text="x",
                max_documents=51,
            )

    def test_network_discovery_requires_explicit_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            discover_issuer_landing_page_documents(
                issuer_key="yuanta", etf_code="0050"
            )

    def test_network_discovery_rejects_protected_source(self) -> None:
        with self.assertRaisesRegex(ValueError, "不允許直接程式查詢"):
            discover_issuer_landing_page_documents(
                issuer_key="blackrock", etf_code="00985D", allow_network=True
            )

    @patch("backend.app.data_sources.issuer_landing_page_discovery.httpx.get")
    def test_network_discovery_parses_official_html(self, mock_get: Mock) -> None:
        response = Mock()
        response.url = "https://www.yuantaetfs.com/News/announcement"
        response.content = "<a href='/docs/0050.pdf'>0050 收益分配公告</a>".encode()
        response.text = response.content.decode()
        response.headers = {"content-type": "text/html; charset=utf-8"}
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = discover_issuer_landing_page_documents(
            issuer_key="yuanta", etf_code="0050", allow_network=True
        )

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].information_basis, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
