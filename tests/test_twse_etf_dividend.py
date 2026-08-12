"""TWSE ETF e添富配息來源測試。"""

import json
import ssl
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.data_sources.registry import (
    SourceType,
    get_data_source,
)
from backend.app.data_sources.twse_etf_dividend import (
    SOURCE_ID,
    extract_twse_dividend_rows,
    fetch_twse_dividend_html,
    save_twse_dividend_html_snapshot,
    validate_twse_dividend_html,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "twse_etf_dividend_sample.html"
)


class TestTWSEETFDividendSource(
    unittest.TestCase
):
    """測試官方配息頁面下載、解析與快照。"""

    def setUp(self) -> None:
        self.html_text = (
            FIXTURE_PATH.read_text(
                encoding="utf-8"
            )
        )

    def test_source_is_registered(
        self,
    ) -> None:
        source = get_data_source(
            SOURCE_ID
        )

        self.assertTrue(
            source.enabled
        )

        self.assertEqual(
            source.source_type,
            SourceType.OFFICIAL_WEB_PAGE,
        )

    def test_page_markers_are_validated(
        self,
    ) -> None:
        validate_twse_dividend_html(
            self.html_text
        )

        with self.assertRaises(
            ValueError
        ):
            validate_twse_dividend_html(
                "<html>invalid</html>"
            )

    def test_rows_are_extracted(
        self,
    ) -> None:
        rows = extract_twse_dividend_rows(
            self.html_text
        )

        self.assertEqual(
            len(rows),
            3,
        )

        self.assertEqual(
            rows[0].etf_code,
            "0050",
        )

        self.assertIn(
            "已實現資本利得占比 74.00 %",
            rows[0].detail_text,
        )

        self.assertIn(
            "已實現資本利得占比 100.00 %",
            rows[1].detail_text,
        )

    @patch(
        "backend.app.data_sources."
        "twse_etf_dividend.httpx.get"
    )
    def test_html_is_downloaded(
        self,
        mock_get: Mock,
    ) -> None:
        response = Mock()
        response.text = self.html_text
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_twse_dividend_html()

        self.assertIn(
            "0050",
            result,
        )

        verify_value = (
            mock_get.call_args.kwargs[
                "verify"
            ]
        )

        self.assertIsInstance(
            verify_value,
            ssl.SSLContext,
        )

    @patch(
        "backend.app.data_sources."
        "twse_etf_dividend.httpx.get"
    )
    def test_historical_query_is_explicit(
        self,
        mock_get: Mock,
    ) -> None:
        response = Mock()
        response.text = self.html_text
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        fetch_twse_dividend_html(
            etf_code=" 00878 ",
            start_year=2023,
            end_year=2023,
        )

        self.assertEqual(
            mock_get.call_args.kwargs["params"],
            {
                "stkNo": "00878",
                "startDate": 2023,
                "endDate": 2023,
            },
        )

    def test_historical_query_rejects_partial_or_invalid_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "同時提供"):
            fetch_twse_dividend_html(start_year=2023)

        with self.assertRaisesRegex(ValueError, "不得早於"):
            fetch_twse_dividend_html(start_year=2024, end_year=2023)

        with self.assertRaisesRegex(ValueError, "代號格式"):
            fetch_twse_dividend_html(etf_code="00878?")

    def test_html_snapshot_is_saved(
        self,
    ) -> None:
        downloaded_at = datetime(
            2026,
            7,
            30,
            6,
            0,
            tzinfo=timezone.utc,
        )

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)

            snapshot = (
                save_twse_dividend_html_snapshot(
                    html_text=self.html_text,
                    output_root=output_root,
                    downloaded_at=downloaded_at,
                )
            )

            self.assertTrue(
                snapshot.data_path.exists()
            )

            self.assertTrue(
                snapshot.metadata_path.exists()
            )

            self.assertTrue(
                (
                    output_root
                    / SOURCE_ID
                    / "latest.html"
                ).exists()
            )

            metadata = json.loads(
                snapshot.metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                metadata["source_id"],
                SOURCE_ID,
            )


if __name__ == "__main__":
    unittest.main()
