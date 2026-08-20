"""M10-4 前端 API client 測試。"""

import unittest
from unittest.mock import Mock, patch

from frontend.api.tax_reinvestment import (
    fetch_tax_reinvestment_scenarios,
)


class TestFrontendTaxReinvestmentClient(unittest.TestCase):
    @patch("frontend.api.transport.httpx.post")
    def test_posts_payload_and_validates_four_scenarios(self, mock_post) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "status": "AVAILABLE",
            "historical_facts": {},
            "calculation": {
                "projection_years": 10,
                "scenarios": [{}, {}, {}, {}],
            },
        }
        mock_post.return_value = response

        result = fetch_tax_reinvestment_scenarios(
            "http://127.0.0.1:8000",
            "0056",
            {"held_units": 1000},
        )

        self.assertEqual(result["status"], "AVAILABLE")
        mock_post.assert_called_once()
        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {"held_units": 1000},
        )
        self.assertTrue(
            mock_post.call_args.args[0].endswith(
                "/api/v1/etfs/0056/tax-reinvestment-scenarios"
            )
        )


if __name__ == "__main__":
    unittest.main()
