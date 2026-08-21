"""SEC-2 tests for redirect-safe frontend transport."""

from pathlib import Path
import unittest
from unittest.mock import patch

import httpx

from frontend.api.errors import APIResponseError
from frontend.api.transport import get_json


class TestFrontendTransportSecurity(unittest.TestCase):
    def test_every_transport_method_disables_redirect_following(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "frontend"
            / "api"
            / "transport.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("follow_redirects=True", source)
        self.assertEqual(5, source.count("follow_redirects=False"))

    @patch("frontend.api.transport.httpx.get")
    def test_custom_headers_are_not_forwarded_through_redirects(self, mock_get) -> None:
        request = httpx.Request("GET", "http://backend/private")
        mock_get.return_value = httpx.Response(
            302,
            headers={"Location": "https://attacker.invalid/capture"},
            request=request,
        )

        with self.assertRaises(APIResponseError):
            get_json(
                "http://backend",
                "/private",
                "private request",
                request_headers={"X-Owner-Token": "session-secret"},
            )

        self.assertFalse(mock_get.call_args.kwargs["follow_redirects"])


if __name__ == "__main__":
    unittest.main()
