"""中信投信最新配息 PDF 探測測試。"""

import unittest
from unittest.mock import patch

from backend.app.data_sources.ctbc_actual_dividend_discovery import (
    build_ctbc_latest_dividend_url,
    discover_ctbc_latest_dividend_document,
)


class TestCtbcActualDividendDiscovery(unittest.TestCase):
    def test_builds_official_pdf_url(self) -> None:
        self.assertEqual(
            build_ctbc_latest_dividend_url(" 00891 "),
            "https://www.ctbcinvestments.com/fund/pdf/"
            "ETFLatestDividend/00891.pdf",
        )

    def test_rejects_path_injection(self) -> None:
        for value in ("../00891", "00891.pdf", "00891?x=1", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_ctbc_latest_dividend_url(value)

    def test_network_requires_explicit_permission(self) -> None:
        with self.assertRaisesRegex(ValueError, "allow_network=True"):
            discover_ctbc_latest_dividend_document(etf_code="00891")

    @patch(
        "backend.app.data_sources.ctbc_actual_dividend_discovery.httpx.head"
    )
    def test_returns_unknown_basis_candidate_without_downloading(
        self, mock_head
    ) -> None:
        response = mock_head.return_value
        response.status_code = 200
        response.url = (
            "https://www.ctbcinvestments.com/fund/pdf/"
            "ETFLatestDividend/00891.pdf"
        )
        response.headers = {
            "content-type": "application/pdf",
            "content-length": "1248453",
        }

        candidate = discover_ctbc_latest_dividend_document(
            etf_code="00891", allow_network=True
        )

        self.assertIsNotNone(candidate)
        assert candidate is not None
        self.assertEqual(candidate.etf_code, "00891")
        self.assertEqual(candidate.information_basis, "UNKNOWN")
        self.assertEqual(candidate.content_length, 1248453)
        mock_head.assert_called_once()

    @patch(
        "backend.app.data_sources.ctbc_actual_dividend_discovery.httpx.head"
    )
    def test_missing_document_returns_none(self, mock_head) -> None:
        response = mock_head.return_value
        response.status_code = 404

        self.assertIsNone(
            discover_ctbc_latest_dividend_document(
                etf_code="00000", allow_network=True
            )
        )

    @patch(
        "backend.app.data_sources.ctbc_actual_dividend_discovery.httpx.head"
    )
    def test_rejects_redirect_outside_official_domains(self, mock_head) -> None:
        response = mock_head.return_value
        response.status_code = 200
        response.url = "https://example.com/00891.pdf"
        response.headers = {"content-type": "application/pdf"}

        with self.assertRaisesRegex(ValueError, "不在允許網域"):
            discover_ctbc_latest_dividend_document(
                etf_code="00891", allow_network=True
            )

    @patch(
        "backend.app.data_sources.ctbc_actual_dividend_discovery.httpx.head"
    )
    def test_rejects_non_pdf_content(self, mock_head) -> None:
        response = mock_head.return_value
        response.status_code = 200
        response.url = "https://www.ctbcinvestments.com/error"
        response.headers = {"content-type": "text/html"}

        with self.assertRaisesRegex(ValueError, "非 PDF"):
            discover_ctbc_latest_dividend_document(
                etf_code="00891", allow_network=True
            )


if __name__ == "__main__":
    unittest.main()
