"""ETF 比較 API 測試。"""

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.api.dependencies import (
    get_database_path,
)
from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.main import create_app


class TestETFComparisonAPI(unittest.TestCase):
    """驗證 ETF 比較 Endpoint。"""

    def setUp(self) -> None:
        """建立隔離應用程式。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )
        self.database_path = (
            Path(self.temp_directory.name)
            / "etf_comparison_api.db"
        )
        initialize_database(
            self.database_path
        )

        connection = get_connection(
            self.database_path
        )

        try:
            connection.executescript(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond,
                    listing_date
                )
                VALUES
                    (
                        '0050',
                        '元大台灣50',
                        0,
                        0,
                        '2003-06-30'
                    ),
                    (
                        '0056',
                        '元大高股息',
                        0,
                        0,
                        '2007-12-26'
                    );
                """
            )
            connection.commit()

        finally:
            connection.close()

        self.application = create_app()
        self.application.dependency_overrides[
            get_database_path
        ] = lambda: self.database_path
        self.client = TestClient(
            self.application
        )

    def tearDown(self) -> None:
        """清理測試資源。"""

        self.client.close()
        self.application.dependency_overrides = {}
        self.temp_directory.cleanup()

    def test_comparison_returns_requested_order(
        self,
    ) -> None:
        """確認回應保留代號順序。"""

        response = self.client.get(
            "/api/v1/etfs/comparison",
            params={
                "codes": "0056,0050",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        data = response.json()
        self.assertEqual(
            data["codes"],
            [
                "0056",
                "0050",
            ],
        )
        self.assertEqual(
            data["items"][0]["etf"][
                "code"
            ],
            "0056",
        )

    def test_one_code_returns_422(
        self,
    ) -> None:
        """確認少於兩檔時拒絕。"""

        response = self.client.get(
            "/api/v1/etfs/comparison",
            params={
                "codes": "0050",
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )

    def test_missing_code_returns_404(
        self,
    ) -> None:
        """確認不存在代號回傳 404。"""

        response = self.client.get(
            "/api/v1/etfs/comparison",
            params={
                "codes": "0050,UNKNOWN",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_openapi_registers_comparison_path(
        self,
    ) -> None:
        """確認 OpenAPI 登錄比較 Endpoint。"""

        self.assertIn(
            "/api/v1/etfs/comparison",
            self.application.openapi()[
                "paths"
            ],
        )


if __name__ == "__main__":
    unittest.main()
