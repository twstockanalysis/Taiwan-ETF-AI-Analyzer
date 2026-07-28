"""ETF 主資料 Endpoint、下載器與快照測試。"""

import json
import ssl
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.data_sources.api_client import (
    fetch_json_records,
    validate_json_records,
)
from backend.app.data_sources.endpoints import (
    DatasetKind,
    build_endpoint_url,
    get_api_endpoint,
)
from backend.app.data_sources.raw_snapshot import (
    save_json_records_snapshot,
)


class TestETFMasterDownload(unittest.TestCase):
    """測試 ETF 主資料下載流程的固定邏輯。"""

    def setUp(self) -> None:
        """取得測試用官方 Endpoint。"""

        self.endpoint = get_api_endpoint(
            "twse_fund_master"
        )

    def test_twse_fund_master_endpoint_exists(
        self,
    ) -> None:
        """確認 TWSE 基金主資料 Endpoint 已登錄。"""

        self.assertEqual(
            self.endpoint.dataset_kind,
            DatasetKind.ETF_MASTER,
        )

        self.assertEqual(
            self.endpoint.source_id,
            "twse_openapi",
        )

    def test_endpoint_url_is_correct(
        self,
    ) -> None:
        """確認正式 API URL 組合正確。"""

        endpoint_url = build_endpoint_url(
            self.endpoint
        )

        self.assertEqual(
            endpoint_url,
            (
                "https://openapi.twse.com.tw/"
                "v1/opendata/t187ap47_L"
            ),
        )

    def test_json_record_list_is_valid(
        self,
    ) -> None:
        """確認 JSON 物件陣列可以通過驗證。"""

        payload = [
            {
                "基金代號": "0050",
                "基金簡稱": "元大台灣50",
            }
        ]

        records = validate_json_records(
            payload
        )

        self.assertEqual(
            len(records),
            1,
        )

        self.assertEqual(
            records[0]["基金代號"],
            "0050",
        )

    def test_non_list_payload_is_rejected(
        self,
    ) -> None:
        """確認最外層不是陣列時被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            validate_json_records(
                {
                    "基金代號": "0050",
                }
            )

    def test_non_object_record_is_rejected(
        self,
    ) -> None:
        """確認陣列元素不是物件時被拒絕。"""

        with self.assertRaises(
            ValueError
        ):
            validate_json_records(
                [
                    {
                        "基金代號": "0050",
                    },
                    "invalid record",
                ]
            )

    @patch(
        "backend.app.data_sources."
        "api_client.httpx.get"
    )
    def test_fetch_json_records(
        self,
        mock_get: Mock,
    ) -> None:
        """確認下載器會解析 HTTP JSON 回應。"""

        response = Mock()

        response.json.return_value = [
            {
                "基金代號": "0050",
                "基金簡稱": "元大台灣50",
            }
        ]

        response.raise_for_status.return_value = (
            None
        )

        mock_get.return_value = response

        records = fetch_json_records(
            self.endpoint
        )

        self.assertEqual(
            records[0]["基金代號"],
            "0050",
        )

        mock_get.assert_called_once()

        verify_value = (
            mock_get.call_args.kwargs[
                "verify"
            ]
        )

        self.assertIsInstance(
            verify_value,
            ssl.SSLContext,
        )

    def test_snapshot_is_saved(
        self,
    ) -> None:
        """確認原始資料及中繼資料可以保存。"""

        records = [
            {
                "基金代號": "0050",
                "基金簡稱": "元大台灣50",
            }
        ]

        downloaded_at = datetime(
            2026,
            7,
            28,
            12,
            0,
            tzinfo=timezone.utc,
        )

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)

            snapshot = (
                save_json_records_snapshot(
                    endpoint=self.endpoint,
                    records=records,
                    output_root=output_root,
                    downloaded_at=downloaded_at,
                )
            )

            self.assertTrue(
                snapshot.data_path.exists()
            )

            self.assertTrue(
                snapshot.metadata_path.exists()
            )

            self.assertEqual(
                snapshot.record_count,
                1,
            )

            latest_data_path = (
                output_root
                / self.endpoint.endpoint_id
                / "latest.json"
            )

            latest_metadata_path = (
                output_root
                / self.endpoint.endpoint_id
                / "latest.meta.json"
            )

            self.assertTrue(
                latest_data_path.exists()
            )

            self.assertTrue(
                latest_metadata_path.exists()
            )

            metadata = json.loads(
                latest_metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                metadata["record_count"],
                1,
            )

            self.assertIn(
                "基金代號",
                metadata[
                    "first_record_keys"
                ],
            )


if __name__ == "__main__":
    unittest.main()