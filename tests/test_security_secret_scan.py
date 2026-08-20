"""Tests for the sanitized SEC-1 secret scanner and ignore contract."""

from pathlib import Path
import subprocess
import unittest

from deployment.security_secret_scan import (
    _is_sensitive_repository_path,
    scan_content,
)


ROOT = Path(__file__).resolve().parents[1]


class TestSecuritySecretScan(unittest.TestCase):
    def test_reports_location_without_exposing_secret(self) -> None:
        secret = "ghp_" + "abcdefghijklmnopqrstuvwxyz123456"
        findings = scan_content(
            f"TOKEN={secret}\n".encode(),
            scope="worktree",
            location="example.env",
        )

        self.assertTrue(any(item.rule == "github-token" for item in findings))
        rendered = "\n".join(str(item) for item in findings)
        self.assertNotIn(secret, rendered)

    def test_detects_repeated_local_owner_token_shape(self) -> None:
        value = "-".join(["privatepart"] * 4)

        findings = scan_content(
            f"TW_ETF_OWNER_TOKEN={value}\n".encode(),
            scope="ignored",
            location="deployment/.env",
        )

        rules = {item.rule for item in findings}
        self.assertIn("repeated-owner-token-shape", rules)
        self.assertIn("generic-secret-assignment", rules)

    def test_allows_documented_placeholder_and_known_test_value(self) -> None:
        content = (
            "TW_ETF_OWNER_TOKEN=replace-with-at-least-32-random-characters\n"
            'OWNER_TOKEN = "correct-owner-token-with-32-bytes!!"\n'
        )

        findings = scan_content(
            content.encode(), scope="tracked", location="example.txt"
        )

        self.assertEqual(set(), findings)

    def test_sensitive_local_artifacts_are_ignored(self) -> None:
        candidates = (
            ".env",
            ".env.local",
            ".streamlit/secrets.toml",
            "deployment/.env",
            "logs/app.log",
            "reports/security.json",
            "database/private.db",
            "backup/config.bak",
            "keys/server.pem",
        )
        for candidate in candidates:
            completed = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", candidate],
                cwd=ROOT,
                check=False,
            )
            with self.subTest(candidate=candidate):
                self.assertEqual(0, completed.returncode)

    def test_sensitive_repository_paths_fail_closed(self) -> None:
        self.assertTrue(_is_sensitive_repository_path(Path("deployment/.env")))
        self.assertTrue(_is_sensitive_repository_path(Path("database/live.db")))
        self.assertTrue(
            _is_sensitive_repository_path(Path(".streamlit/secrets.toml"))
        )
        self.assertFalse(
            _is_sensitive_repository_path(Path("deployment/.env.example"))
        )


if __name__ == "__main__":
    unittest.main()
