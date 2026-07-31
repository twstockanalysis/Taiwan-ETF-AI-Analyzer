"""M8 最終架構契約 Smoke Tests。"""

import tempfile
import unittest
from pathlib import Path

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "etf_master",
    "import_batch",
    "etf_performance",
    "etf_dividend",
    "etf_dividend_component",
    "dividend_source_document",
    "dividend_source_review_queue",
}

EXPECTED_API_PATHS = {
    "/",
    "/health",
    "/api/v1/etfs",
    "/api/v1/etfs/{code}",
    "/api/v1/performance/ranking",
    "/api/v1/etfs/{code}/performance",
    "/api/v1/etfs/{code}/dividends",
    "/api/v1/etfs/{code}/dividends/76w",
    "/api/v1/dividends/{dividend_id}",
    "/api/v1/dividends/{dividend_id}/components",
    (
        "/api/v1/data-quality/dividends/"
        "actual-coverage"
    ),
    (
        "/api/v1/data-quality/dividends/"
        "review-queue"
    ),
    (
        "/api/v1/data-quality/dividends/"
        "review-queue/{queue_id}"
    ),
}

FRONTEND_MARKERS = {
    'title="首頁"',
    'url_path="etf-search"',
    'url_path="performance-ranking"',
    'url_path="dividend-data-quality"',
    'url_path="etf-detail"',
    'hidden=True',
}


class TestM8ArchitectureSmoke(
    unittest.TestCase
):
    """驗證 M8 最終架構的跨模組契約。"""

    def test_fresh_database_has_all_m8_tables(
        self,
    ) -> None:
        """全新資料庫必須包含 M8 完整資料表。"""

        with tempfile.TemporaryDirectory() as directory:
            database_path = (
                Path(directory)
                / "m8_smoke.db"
            )

            initialize_database(
                database_path
            )

            connection = get_connection(
                database_path
            )

            try:
                rows = connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                      AND name NOT LIKE 'sqlite_%';
                    """
                ).fetchall()

                table_names = {
                    row["name"]
                    for row in rows
                }

                self.assertTrue(
                    EXPECTED_TABLES.issubset(
                        table_names
                    )
                )

                violations = connection.execute(
                    """
                    PRAGMA foreign_key_check;
                    """
                ).fetchall()

                self.assertEqual(
                    violations,
                    [],
                )

            finally:
                connection.close()

    def test_openapi_registers_all_m8_routes(
        self,
    ) -> None:
        """FastAPI OpenAPI 必須登錄 M8 全部路徑。"""

        from backend.app.main import (
            create_app,
        )

        paths = set(
            create_app()
            .openapi()["paths"]
        )

        self.assertTrue(
            EXPECTED_API_PATHS.issubset(
                paths
            )
        )

    def test_frontend_navigation_registers_m8_pages(
        self,
    ) -> None:
        """Streamlit 入口必須登錄主要頁面與隱藏詳細頁。"""

        source = (
            PROJECT_ROOT
            / "frontend"
            / "navigation.py"
        ).read_text(
            encoding="utf-8"
        )

        for marker in FRONTEND_MARKERS:
            with self.subTest(
                marker=marker
            ):
                self.assertIn(
                    marker,
                    source,
                )

    def test_markdown_fences_are_balanced(
        self,
    ) -> None:
        """所有文件的 Markdown 程式碼區塊必須成對。"""

        docs_directory = (
            PROJECT_ROOT / "docs"
        )

        for path in sorted(
            docs_directory.glob("*.md")
        ):
            content = path.read_text(
                encoding="utf-8"
            )

            with self.subTest(
                document=path.name
            ):
                self.assertEqual(
                    content.count("```") % 2,
                    0,
                )

                self.assertTrue(
                    content.strip(),
                )


if __name__ == "__main__":
    unittest.main()
