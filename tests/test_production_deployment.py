"""Static deployment-contract tests."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestProductionDeployment(unittest.TestCase):
    def test_compose_keeps_apps_private_and_mounts_durable_database(self) -> None:
        compose = (ROOT / "deployment/compose.yaml").read_text(encoding="utf-8")
        self.assertIn("TW_ETF_DATABASE_PATH: /data/tw_etf.db", compose)
        self.assertIn("TW_ETF_OWNER_TOKEN", compose)
        self.assertNotIn('"8000:8000"', compose)
        self.assertNotIn('"8501:8501"', compose)
        self.assertIn('"443:443"', compose)

    def test_secrets_are_ignored_and_example_is_placeholder(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        example = (ROOT / "deployment/.env.example").read_text(encoding="utf-8")
        self.assertIn("deployment/.env", ignore)
        self.assertIn("replace-with", example)
        self.assertNotIn("correct-owner-token", example)

    def test_docker_context_is_allowlisted_to_runtime_source(self) -> None:
        dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
        self.assertIn("**\n", dockerignore)
        self.assertIn("!requirements.lock", dockerignore)
        self.assertIn("!backend/**", dockerignore)
        self.assertIn("!frontend/**", dockerignore)
        self.assertNotIn("!database/", dockerignore)
        self.assertNotIn("!deployment/", dockerignore)

    def test_locked_versions_match_verified_environment(self) -> None:
        locked = (ROOT / "requirements.lock").read_text(encoding="utf-8")
        self.assertIn("fastapi[standard]==0.140.7", locked)
        self.assertIn("streamlit==1.60.0", locked)


if __name__ == "__main__":
    unittest.main()
