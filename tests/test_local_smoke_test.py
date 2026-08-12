"""Tests for native local deployment smoke result semantics."""

import json
import unittest
from unittest.mock import patch

from deployment.local_smoke_test import run_smoke


class TestLocalSmokeTest(unittest.TestCase):
    @patch("deployment.local_smoke_test.request")
    def test_all_required_boundaries_pass(self, request) -> None:
        request.side_effect = [
            (200, json.dumps({"status": "healthy"}).encode()),
            (401, b""),
            (401, b""),
            (200, b"{}"),
            (200, b"html"),
            (200, b"ok"),
        ]
        results = run_smoke(
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8501",
            "local-owner-token-with-32-characters",
        )
        self.assertTrue(all(results.values()))

    @patch("deployment.local_smoke_test.request")
    def test_anonymous_private_success_is_a_failure(self, request) -> None:
        request.side_effect = [
            (200, b'{"status":"healthy"}'),
            (200, b"{}"),
            (401, b""),
            (200, b"{}"),
            (200, b"html"),
            (200, b"ok"),
        ]
        results = run_smoke("http://api", "http://frontend", "owner-token")
        self.assertFalse(results["anonymous_private_denied"])


if __name__ == "__main__":
    unittest.main()
