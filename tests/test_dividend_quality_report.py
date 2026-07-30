"""ETF 配息產物與品質報告測試。"""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backend.app.data_sources.dividend_normalizer import (
    normalize_twse_dividend_html,
)
from backend.app.data_sources.dividend_quality_report import (
    DividendPipelineIssue,
    build_dividend_quality_report,
    save_dividend_artifacts,
    save_dividend_quality_report,
)
from backend.app.data_sources.twse_etf_dividend import (
    save_twse_dividend_html_snapshot,
)
from backend.app.repositories.dividend_repository import (
    DividendComponentUpsertSummary,
    DividendDatasetUpsertSummary,
    DividendUpsertSummary,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "twse_etf_dividend_sample.html"
)


class TestDividendQualityReport(
    unittest.TestCase
):
    """測試配息 JSON 產物與品質摘要。"""

    def setUp(self) -> None:
        """準備固定正規化結果。"""

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.temp_path = Path(
            self.temp_directory.name
        )

        self.created_at = datetime(
            2026,
            7,
            30,
            8,
            0,
            tzinfo=timezone.utc,
        )

        self.html_text = (
            FIXTURE_PATH.read_text(
                encoding="utf-8"
            )
        )

        self.result = (
            normalize_twse_dividend_html(
                self.html_text
            )
        )

        self.issues = [
            DividendPipelineIssue(
                category="normalization",
                row_number=issue.row_number,
                etf_code=issue.etf_code,
                reason=issue.reason,
            )
            for issue in self.result.rejected
        ]

        self.import_summary = (
            DividendDatasetUpsertSummary(
                dividends=(
                    DividendUpsertSummary(
                        total_records=2,
                        inserted_records=2,
                        updated_records=0,
                    )
                ),
                components=(
                    DividendComponentUpsertSummary(
                        total_records=10,
                        inserted_records=10,
                        updated_records=0,
                    )
                ),
            )
        )

    def tearDown(self) -> None:
        """清除臨時目錄。"""

        self.temp_directory.cleanup()

    def build_report(self):
        """建立產物與品質報告。"""

        raw_snapshot = (
            save_twse_dividend_html_snapshot(
                html_text=self.html_text,
                output_root=(
                    self.temp_path / "raw"
                ),
                downloaded_at=(
                    self.created_at
                ),
            )
        )

        artifacts = save_dividend_artifacts(
            batch_id=1,
            source_id=(
                "twse_etfortune_dividend"
            ),
            result=self.result,
            issues=self.issues,
            processed_root=(
                self.temp_path / "processed"
            ),
            rejected_root=(
                self.temp_path / "rejected"
            ),
            created_at=self.created_at,
        )

        report = build_dividend_quality_report(
            batch_id=1,
            source_id=(
                "twse_etfortune_dividend"
            ),
            raw_record_count=3,
            raw_snapshot=raw_snapshot,
            result=self.result,
            issues=self.issues,
            import_summary=(
                self.import_summary
            ),
            artifact_paths=artifacts,
        )

        return report, artifacts

    def test_artifacts_contain_events_and_components(
        self,
    ) -> None:
        """確認 Processed 檔案分開保存事件與組成。"""

        _, artifacts = self.build_report()

        payload = json.loads(
            artifacts.processed_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            len(payload["dividends"]),
            2,
        )

        self.assertEqual(
            len(payload["components"]),
            10,
        )

        rejected = json.loads(
            artifacts.rejected_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            len(rejected),
            1,
        )

    def test_report_counts_are_correct(
        self,
    ) -> None:
        """確認品質報告統計正確。"""

        report, _ = self.build_report()

        self.assertEqual(
            report["raw_record_count"],
            3,
        )

        self.assertEqual(
            report[
                "accepted_dividend_count"
            ],
            2,
        )

        self.assertEqual(
            report[
                "accepted_component_count"
            ],
            10,
        )

        self.assertEqual(
            report["rejected_record_count"],
            1,
        )

        self.assertEqual(
            report["acceptance_rate"],
            0.666667,
        )

    def test_report_preserves_estimated_semantics(
        self,
    ) -> None:
        """確認預估資本利得與實際 76W 分離。"""

        report, _ = self.build_report()

        self.assertEqual(
            report[
                "estimated_realized_gain_count"
            ],
            2,
        )

        self.assertEqual(
            report["actual_76w_count"],
            0,
        )

        self.assertEqual(
            report["warnings"],
            [],
        )

    def test_report_file_and_latest_are_saved(
        self,
    ) -> None:
        """確認報告歷史檔與 latest 同時保存。"""

        report, _ = self.build_report()

        report_path = (
            save_dividend_quality_report(
                batch_id=1,
                source_id=(
                    "twse_etfortune_dividend"
                ),
                report=report,
                output_root=(
                    self.temp_path / "reports"
                ),
                created_at=(
                    self.created_at
                ),
            )
        )

        latest_path = (
            self.temp_path
            / "reports"
            / "twse_etfortune_dividend"
            / "latest.json"
        )

        self.assertTrue(
            report_path.exists()
        )

        self.assertTrue(
            latest_path.exists()
        )


if __name__ == "__main__":
    unittest.main()
