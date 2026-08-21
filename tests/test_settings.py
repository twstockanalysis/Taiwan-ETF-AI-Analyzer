"""Tests for deployment path configuration."""

from pathlib import Path
import unittest

from backend.app.config.settings import (
    DATABASE_DIR,
    DATABASE_PATH_ENV,
    resolve_database_path,
)


class TestSettings(unittest.TestCase):
    def test_database_path_keeps_development_default(self) -> None:
        self.assertEqual(resolve_database_path({}), DATABASE_DIR / "tw_etf.db")

    def test_database_path_accepts_absolute_durable_path(self) -> None:
        configured = str(Path.cwd().resolve() / "tw-etf-data" / "tw_etf.db")

        result = resolve_database_path({DATABASE_PATH_ENV: configured})

        self.assertTrue(result.is_absolute())
        self.assertEqual(result.name, "tw_etf.db")

    def test_database_path_rejects_relative_deployment_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "絕對路徑"):
            resolve_database_path({DATABASE_PATH_ENV: "data/tw_etf.db"})


if __name__ == "__main__":
    unittest.main()
