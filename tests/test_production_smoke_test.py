"""Production smoke test security and result tests."""

import json
import unittest
from unittest.mock import patch

from deployment.smoke_test import _NoRedirectHandler, run_smoke


class TestProductionSmokeTest(unittest.TestCase):
    def test_redirect_handler_refuses_every_redirect(self) -> None:
        handler = _NoRedirectHandler()
        self.assertIsNone(
            handler.redirect_request(
                object(),
                None,
                302,
                "Found",
                {},
                "https://attacker.invalid/",
            )
        )

    @patch("deployment.smoke_test.request")
    def test_all_required_boundaries_pass(self, request) -> None:
        request.side_effect = [
            (200, json.dumps({"status": "healthy"}).encode()),
            (401, b""),
            (200, b"{}"),
            (200, b"html"),
        ]
        results = run_smoke(
            "https://etf.example.com",
            "x" * 32,
        )
        self.assertTrue(all(results.values()))

    @patch("deployment.smoke_test.request")
    def test_owner_redirect_is_not_accepted(self, request) -> None:
        request.side_effect = [
            (200, b'{"status":"healthy"}'),
            (401, b""),
            (302, b""),
            (200, b"html"),
        ]
        results = run_smoke("https://etf.example.com", "x" * 32)
        self.assertFalse(results["owner_private_allowed"])


if __name__ == "__main__":
    unittest.main()
