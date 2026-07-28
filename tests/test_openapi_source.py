"""OpenAPI 下載與端點探索測試。"""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.data_sources.openapi import (
    fetch_openapi_document,
    find_endpoint_candidates,
    resolve_base_url,
    save_openapi_snapshot,
    validate_openapi_document,
)
from backend.app.data_sources.registry import (
    get_data_source,
)


class TestOpenAPISource(unittest.TestCase):
    """測試 OpenAPI 規格處理。"""

    def build_document(
        self,
    ) -> dict:
        """建立 Swagger 2 測試文件。"""

        return {
            "swagger": "2.0",
            "host": "example.test",
            "basePath": "/v1",
            "schemes": ["https"],
            "paths": {
                "/etfs": {
                    "get": {
                        "summary": (
                            "取得 ETF 商品清單"
                        ),
                        "operationId": (
                            "listEtfs"
                        ),
                        "tags": ["ETF"],
                    }
                },
                "/stocks": {
                    "get": {
                        "summary": (
                            "取得股票清單"
                        ),
                        "operationId": (
                            "listStocks"
                        ),
                        "tags": ["Stocks"],
                    }
                },
            },
        }

    def test_valid_document_is_accepted(
        self,
    ) -> None:
        """確認合法規格可以通過。"""

        document = self.build_document()

        result = validate_openapi_document(
            document
        )

        self.assertEqual(
            result["swagger"],
            "2.0",
        )

    def test_invalid_document_is_rejected(
        self,
    ) -> None:
        """確認缺少 paths 的文件被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            validate_openapi_document(
                {
                    "swagger": "2.0",
                }
            )

    def test_base_url_is_resolved(
        self,
    ) -> None:
        """確認 Swagger 2 Base URL。"""

        result = resolve_base_url(
            self.build_document()
        )

        self.assertEqual(
            result,
            "https://example.test/v1",
        )

    def test_etf_endpoint_is_discovered(
        self,
    ) -> None:
        """確認可找到 ETF 候選端點。"""

        candidates = (
            find_endpoint_candidates(
                document=self.build_document(),
                keywords=("ETF",),
            )
        )

        self.assertEqual(
            len(candidates),
            1,
        )
        self.assertEqual(
            candidates[0].path,
            "/etfs",
        )

    def test_snapshot_is_saved(
        self,
    ) -> None:
        """確認規格及中繼資料可儲存。"""

        source = get_data_source(
            "twse_openapi"
        )

        downloaded_at = datetime(
            2026,
            7,
            28,
            10,
            0,
            tzinfo=timezone.utc,
        )

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)

            snapshot = save_openapi_snapshot(
                source=source,
                document=self.build_document(),
                output_root=output_root,
                downloaded_at=downloaded_at,
            )

            self.assertTrue(
                snapshot.document_path.exists()
            )
            self.assertTrue(
                snapshot.metadata_path.exists()
            )
            self.assertEqual(
                snapshot.path_count,
                2,
            )

            latest_path = (
                output_root
                / source.source_id
                / "latest.json"
            )

            self.assertTrue(
                latest_path.exists()
            )

    @patch(
        "backend.app.data_sources."
        "openapi.httpx.get"
    )
    def test_fetch_uses_http_client(
        self,
        mock_get: Mock,
    ) -> None:
        """確認下載器解析 JSON 回應。"""

        response = Mock()
        response.json.return_value = (
            self.build_document()
        )
        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        result = fetch_openapi_document(
            "https://example.test/swagger.json"
        )

        self.assertIn(
            "/etfs",
            result["paths"],
        )

        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()