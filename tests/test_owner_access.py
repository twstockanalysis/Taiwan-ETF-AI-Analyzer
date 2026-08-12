"""Security tests for the M12-4 owner-only API boundary."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.owner_access import OWNER_TOKEN_ENV
from backend.app.api.dependencies import get_database_path
from backend.app.database.init_db import initialize_database
from backend.app.main import create_app


class TestOwnerAccess(unittest.TestCase):
    OWNER_TOKEN = "correct-owner-token-with-32-bytes!!"
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_directory.name) / "owner.db"
        initialize_database(self.database)
        self.application = create_app()
        self.application.dependency_overrides[get_database_path] = lambda: self.database
        self.client = TestClient(self.application)

    def tearDown(self) -> None:
        self.client.close()
        self.application.dependency_overrides.clear()
        self.temp_directory.cleanup()

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_server_token_fails_closed(self) -> None:
        response = self.client.get("/api/v1/decision-profile")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("X-Owner-Token", response.text)

    @patch.dict(os.environ, {OWNER_TOKEN_ENV: "too-short"}, clear=True)
    def test_short_server_token_is_misconfigured(self) -> None:
        response = self.client.get(
            "/api/v1/decision-profile",
            headers={"X-Owner-Token": "too-short"},
        )
        self.assertEqual(response.status_code, 503)

    @patch.dict(os.environ, {OWNER_TOKEN_ENV: OWNER_TOKEN}, clear=True)
    def test_missing_or_wrong_token_is_unauthorized(self) -> None:
        missing = self.client.get("/api/v1/decision-profile")
        wrong = self.client.get(
            "/api/v1/decision-profile",
            headers={"X-Owner-Token": "wrong-owner-token"},
        )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(wrong.headers["www-authenticate"], "OwnerToken")
        self.assertNotIn(self.OWNER_TOKEN, wrong.text)

    @patch.dict(os.environ, {OWNER_TOKEN_ENV: OWNER_TOKEN}, clear=True)
    def test_correct_token_passes_gate_and_public_health_stays_public(self) -> None:
        protected = self.client.get(
            "/api/v1/decision-profile",
            headers={"X-Owner-Token": self.OWNER_TOKEN},
        )
        health = self.client.get("/health")
        self.assertEqual(protected.status_code, 200)
        self.assertEqual(health.status_code, 200)


if __name__ == "__main__":
    unittest.main()
