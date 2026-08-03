"""ETF 資料來源與新鮮度 API 測試。"""

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


class TestETFDataProfileAPI(
    unittest.TestCase
):
    """測試單一 ETF 資料概況 Endpoint。"""

    def setUp(self) -> None:
        """建立獨立測試應用程式。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(self.temp_directory.name)
            / "etf_data_profile_api.db"
        )

        initialize_database(
            self.database_path
        )

        connection = get_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond,
                    listing_date
                )
                VALUES (
                    '0050',
                    '元大台灣50',
                    0,
                    0,
                    '2003-06-30'
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
        """關閉測試用戶端。"""

        self.client.close()
        self.application.dependency_overrides = {}
        self.temp_directory.cleanup()

    def test_profile_returns_empty_sections(
        self,
    ) -> None:
        """確認只有主資料時回傳合法缺資料語意。"""

        response = self.client.get(
            "/api/v1/etfs/0050/data-profile"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            data["etf_code"],
            "0050",
        )

        self.assertEqual(
            data["performance"][
                "record_count"
            ],
            0,
        )

        self.assertIsNone(
            data["performance"][
                "latest_as_of_date"
            ]
        )

        self.assertEqual(
            data["dividends"][
                "event_count"
            ],
            0,
        )

        self.assertEqual(
            data["actual_dividend"][
                "actual_76w_event_count"
            ],
            0,
        )

    def test_missing_etf_returns_404(
        self,
    ) -> None:
        """確認不存在 ETF 回傳 404。"""

        response = self.client.get(
            "/api/v1/etfs/UNKNOWN/data-profile"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertIn(
            "UNKNOWN",
            response.json()["detail"],
        )

    def test_openapi_registers_profile_path(
        self,
    ) -> None:
        """確認 OpenAPI 登錄資料概況 Endpoint。"""

        paths = set(
            self.application
            .openapi()["paths"]
        )

        self.assertIn(
            "/api/v1/etfs/{code}/data-profile",
            paths,
        )


if __name__ == "__main__":
    unittest.main()
