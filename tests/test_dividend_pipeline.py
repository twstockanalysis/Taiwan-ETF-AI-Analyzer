"""TWSE ETF 配息完整 Pipeline 測試。"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app.database.connection import (
    get_connection,
)
from backend.app.database.init_db import (
    initialize_database,
)
from backend.app.data_sources.dividend_pipeline import (
    run_dividend_pipeline,
)
from backend.app.repositories.import_batch_repository import (
    get_latest_import_batch,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "twse_etf_dividend_sample.html"
)


class TestDividendPipeline(
    unittest.TestCase
):
    """測試配息下載、正規化、匯入與品質報告。"""

    def setUp(self) -> None:
        """建立獨立資料庫與輸出目錄。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.database_path = (
            self.temp_path
            / "dividend_pipeline.db"
        )

        self.raw_root = (
            self.temp_path / "raw"
        )

        self.processed_root = (
            self.temp_path / "processed"
        )

        self.rejected_root = (
            self.temp_path / "rejected"
        )

        self.report_root = (
            self.temp_path / "reports"
        )

        self.html_text = (
            FIXTURE_PATH.read_text(
                encoding="utf-8"
            )
        )

        self.run_at = datetime(
            2026,
            7,
            30,
            8,
            0,
            tzinfo=timezone.utc,
        )

        initialize_database(
            self.database_path
        )

    def tearDown(self) -> None:
        """清除臨時資料。"""

        self.temp_directory.cleanup()

    def insert_etfs(
        self,
        codes: tuple[str, ...],
    ) -> None:
        """建立 Pipeline 所需 ETF 主資料。"""

        connection = get_connection(
            self.database_path
        )

        try:
            connection.executemany(
                """
                INSERT INTO etf_master (
                    code,
                    name,
                    is_active,
                    is_bond
                )
                VALUES (?, ?, ?, ?);
                """,
                [
                    (
                        code,
                        f"{code} 測試 ETF",
                        0,
                        0,
                    )
                    for code in codes
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def run_pipeline(self):
        """使用固定 Fixture 執行 Pipeline。"""

        return run_dividend_pipeline(
            database_path=self.database_path,
            raw_output_root=self.raw_root,
            processed_output_root=(
                self.processed_root
            ),
            rejected_output_root=(
                self.rejected_root
            ),
            report_output_root=(
                self.report_root
            ),
            html_text=self.html_text,
            run_at=self.run_at,
        )

    def test_successful_pipeline(
        self,
    ) -> None:
        """確認事件、組成、產物與批次成功寫入。"""

        self.insert_etfs(
            (
                "0050",
                "00930",
                "00940",
            )
        )

        result = self.run_pipeline()

        self.assertEqual(
            result.raw_record_count,
            3,
        )

        self.assertEqual(
            result.accepted_dividend_count,
            2,
        )

        self.assertEqual(
            result.accepted_component_count,
            10,
        )

        self.assertEqual(
            result.rejected_record_count,
            1,
        )

        self.assertEqual(
            result.inserted_dividend_count,
            2,
        )

        self.assertEqual(
            result.inserted_component_count,
            10,
        )

        self.assertTrue(
            result.raw_snapshot_path.exists()
        )

        self.assertTrue(
            result.processed_path.exists()
        )

        self.assertTrue(
            result.rejected_path.exists()
        )

        self.assertTrue(
            result.quality_report_path.exists()
        )

        connection = get_connection(
            self.database_path
        )

        try:
            dividend_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend;
                """
            ).fetchone()["total"]

            component_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend_component;
                """
            ).fetchone()["total"]

            actual_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend_component
                WHERE component_basis = 'ACTUAL';
                """
            ).fetchone()["total"]

            code_76w_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend_component
                WHERE component_code = '76W';
                """
            ).fetchone()["total"]

        finally:
            connection.close()

        self.assertEqual(
            dividend_count,
            2,
        )

        self.assertEqual(
            component_count,
            10,
        )

        self.assertEqual(
            actual_count,
            0,
        )

        self.assertEqual(
            code_76w_count,
            0,
        )

        batch = get_latest_import_batch(
            self.database_path
        )

        self.assertEqual(
            batch["status"],
            "success",
        )

        self.assertEqual(
            batch["accepted_record_count"],
            2,
        )

        self.assertEqual(
            batch["inserted_record_count"],
            12,
        )

    def test_repeated_pipeline_updates_in_place(
        self,
    ) -> None:
        """確認重複執行不會建立重複資料。"""

        self.insert_etfs(
            (
                "0050",
                "00930",
                "00940",
            )
        )

        first_result = self.run_pipeline()
        second_result = self.run_pipeline()

        self.assertEqual(
            first_result.inserted_dividend_count,
            2,
        )

        self.assertEqual(
            second_result.inserted_dividend_count,
            0,
        )

        self.assertEqual(
            second_result.updated_dividend_count,
            2,
        )

        self.assertEqual(
            second_result.inserted_component_count,
            0,
        )

        self.assertEqual(
            second_result.updated_component_count,
            10,
        )

        connection = get_connection(
            self.database_path
        )

        try:
            dividend_count = connection.execute(
                "SELECT COUNT(*) FROM etf_dividend;"
            ).fetchone()[0]

            component_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM etf_dividend_component;
                """
            ).fetchone()[0]

        finally:
            connection.close()

        self.assertEqual(
            dividend_count,
            2,
        )

        self.assertEqual(
            component_count,
            10,
        )

    def test_missing_master_etf_is_rejected(
        self,
    ) -> None:
        """確認未知 ETF 不會使整批失敗。"""

        self.insert_etfs(
            (
                "0050",
            )
        )

        result = self.run_pipeline()

        self.assertEqual(
            result.accepted_dividend_count,
            1,
        )

        self.assertEqual(
            result.accepted_component_count,
            5,
        )

        self.assertEqual(
            result.rejected_record_count,
            2,
        )

        rejected_payload = json.loads(
            result.rejected_path.read_text(
                encoding="utf-8"
            )
        )

        categories = {
            item["category"]
            for item in rejected_payload
        }

        self.assertEqual(
            categories,
            {
                "normalization",
                "missing_etf_master",
            },
        )

        self.assertTrue(
            any(
                item["etf_code"] == "00930"
                and item["category"]
                == "missing_etf_master"
                for item in rejected_payload
            )
        )

        batch = get_latest_import_batch(
            self.database_path
        )

        self.assertEqual(
            batch["status"],
            "success",
        )

    def test_quality_report_separates_estimated_gain(
        self,
    ) -> None:
        """確認品質報告不把預估資本利得視為 76W。"""

        self.insert_etfs(
            (
                "0050",
                "00930",
                "00940",
            )
        )

        result = self.run_pipeline()

        report = json.loads(
            result.quality_report_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            report[
                "estimated_component_count"
            ],
            10,
        )

        self.assertEqual(
            report[
                "estimated_realized_gain_count"
            ],
            2,
        )

        self.assertEqual(
            report["actual_component_count"],
            0,
        )

        self.assertEqual(
            report["actual_76w_count"],
            0,
        )

        self.assertIn(
            "EST_REALIZED_CAPITAL_GAIN",
            report["notes"],
        )


    def test_conflicting_duplicate_components_are_rejected(
        self,
    ) -> None:
        """相同事件的矛盾預估組成不得任選一組。"""

        self.insert_etfs(
            (
                "0050",
                "00930",
                "00940",
            )
        )

        duplicate_event_html = """
    <tr>
      <td>0050</td>
      <td>元大台灣50</td>
      <td>115年07月21日</td>
      <td>115年07月27日</td>
      <td>115年08月10日</td>
      <td>0.6</td>
      <td>詳細資料</td>
    </tr>
    <tr class="detail">
      <td colspan="7">
        預估收益分配組成占比資訊：
        (1)股利所得占比 100.00 %
        (2)利息所得占比 0.00 %
        (3)收益平準金占比 0.00 %
        (4)已實現資本利得占比 0.00 %
        (5)其他所得占比 0.00 %
      </td>
    </tr>
"""

        html_text = self.html_text.replace(
            "</tbody>",
            duplicate_event_html
            + "</tbody>",
        )

        result = run_dividend_pipeline(
            database_path=self.database_path,
            raw_output_root=self.raw_root,
            processed_output_root=(
                self.processed_root
            ),
            rejected_output_root=(
                self.rejected_root
            ),
            report_output_root=(
                self.report_root
            ),
            html_text=html_text,
            run_at=self.run_at,
        )

        self.assertEqual(
            result.raw_record_count,
            4,
        )

        self.assertEqual(
            result.accepted_dividend_count,
            2,
        )

        self.assertEqual(
            result.accepted_component_count,
            5,
        )

        rejected_payload = json.loads(
            result.rejected_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(
            any(
                item["category"]
                == (
                    "conflicting_component_disclosure"
                )
                and item["etf_code"] == "0050"
                for item in rejected_payload
            )
        )

        connection = get_connection(
            self.database_path
        )

        try:
            event_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend
                WHERE etf_code = '0050';
                """
            ).fetchone()["total"]

            component_count = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM etf_dividend_component AS c
                INNER JOIN etf_dividend AS d
                    ON d.id = c.dividend_id
                WHERE d.etf_code = '0050';
                """
            ).fetchone()["total"]

        finally:
            connection.close()

        self.assertEqual(
            event_count,
            1,
        )

        self.assertEqual(
            component_count,
            0,
        )


    @patch(
        "backend.app.data_sources."
        "dividend_pipeline."
        "fetch_twse_dividend_html"
    )
    def test_download_failure_is_recorded(
        self,
        mock_fetch,
    ) -> None:
        """確認下載錯誤會留下 failed 批次。"""

        mock_fetch.side_effect = RuntimeError(
            "模擬配息下載失敗"
        )

        with self.assertRaises(
            RuntimeError
        ):
            run_dividend_pipeline(
                database_path=(
                    self.database_path
                ),
                raw_output_root=(
                    self.raw_root
                ),
                processed_output_root=(
                    self.processed_root
                ),
                rejected_output_root=(
                    self.rejected_root
                ),
                report_output_root=(
                    self.report_root
                ),
                run_at=self.run_at,
            )

        batch = get_latest_import_batch(
            self.database_path
        )

        self.assertEqual(
            batch["status"],
            "failed",
        )

        self.assertIn(
            "模擬配息下載失敗",
            batch["error_message"],
        )


if __name__ == "__main__":
    unittest.main()
