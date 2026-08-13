"""摩根投信配息實際配發 PDF 發現測試。"""

import unittest
from unittest.mock import Mock, patch

from backend.app.data_sources.jpmorgan_actual_dividend_discovery import (
    discover_jpmorgan_dividend_documents,
    parse_jpmorgan_dividend_documents,
)


class TestJPMorganActualDividendDiscovery(unittest.TestCase):
    def test_target_group_accepts_actual_pdf_only(self) -> None:
        result = parse_jpmorgan_dividend_documents(
            etf_code="00401A",
            html_text="""
            <a href="/fund/00401a">00401A摩根台灣鑫收益主動式ETF</a>
            <a href="https://am.jpmorgan.com/documents/actual.pdf">
              摩根台灣鑫收益主動式ETF基金配息實際配發公告稿
            </a>
            <a href="https://am.jpmorgan.com/documents/estimated.pdf">
              摩根台灣鑫收益主動式ETF基金配息公告稿
            </a>
            <a href="/fund/00989a">00989A摩根美國科技主動式ETF</a>
            <a href="https://am.jpmorgan.com/documents/other.pdf">
              摩根美國科技ETF基金配息實際配發公告稿
            </a>
            """,
        )

        self.assertEqual(len(result), 1)
        self.assertIn("actual.pdf", result[0].document_url)
        self.assertEqual(result[0].information_basis, "UNKNOWN")

    def test_network_discovery_requires_explicit_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            discover_jpmorgan_dividend_documents(etf_code="00401A")

    @patch(
        "backend.app.data_sources.jpmorgan_actual_dividend_discovery.httpx.get"
    )
    def test_network_discovery_reads_official_html(self, mock_get: Mock) -> None:
        response = Mock()
        response.url = (
            "https://am.jpmorgan.com/tw/zh/asset-management/twetf/"
            "funds/announcements/"
        )
        response.content = b"<html></html>"
        response.text = "<html></html>"
        response.headers = {"content-type": "text/html; charset=utf-8"}
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        result = discover_jpmorgan_dividend_documents(
            etf_code="00401A", allow_network=True
        )

        self.assertEqual(result, ())


if __name__ == "__main__":
    unittest.main()
