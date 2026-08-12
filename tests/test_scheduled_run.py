"""Tests for the locked declarative scheduled-run executor."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from backend.app.operations.scheduled_run import run_schedule


class TestScheduledRun(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.config = self.root / "schedule.json"
        self.report = self.root / "latest.json"
        self.lock = self.root / "schedule.lock"
        self.logs = self.root / "logs"

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _write_jobs(self) -> None:
        self.config.write_text(
            json.dumps({"jobs": [
                {"name": "first", "argv": ["python", "first"]},
                {"name": "second", "argv": ["python", "second"]},
            ]}),
            encoding="utf-8",
        )

    @patch("backend.app.operations.scheduled_run.subprocess.run")
    def test_success_writes_report_logs_and_removes_lock(self, run) -> None:
        self._write_jobs()
        run.return_value = subprocess.CompletedProcess([], 0, "done", "")

        report = run_schedule(self.config, self.report, self.lock, self.logs)

        self.assertEqual(report.status, "success")
        self.assertEqual(run.call_count, 2)
        self.assertFalse(self.lock.exists())
        self.assertEqual(json.loads(self.report.read_text())["status"], "success")
        self.assertEqual(len(list(self.logs.glob("*.log"))), 2)
        self.assertFalse(run.call_args.kwargs["shell"])

    @patch("backend.app.operations.scheduled_run.subprocess.run")
    def test_failure_stops_remaining_jobs_and_reports_failure(self, run) -> None:
        self._write_jobs()
        run.return_value = subprocess.CompletedProcess([], 7, "", "failed")

        report = run_schedule(self.config, self.report, self.lock, self.logs)

        self.assertEqual(report.status, "failed")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(report.jobs[0].exit_code, 7)
        self.assertFalse(self.lock.exists())

    def test_existing_lock_refuses_overlapping_run(self) -> None:
        self._write_jobs()
        self.lock.touch()
        with self.assertRaisesRegex(RuntimeError, "正在執行"):
            run_schedule(self.config, self.report, self.lock, self.logs)

    def test_invalid_empty_schedule_is_rejected(self) -> None:
        self.config.write_text('{"jobs": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "至少一個"):
            run_schedule(self.config, self.report, self.lock, self.logs)

    def test_unsafe_job_name_is_rejected_and_lock_is_removed(self) -> None:
        self.config.write_text(
            json.dumps({"jobs": [{"name": "../escape", "argv": ["python"]}]}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "job 名稱"):
            run_schedule(self.config, self.report, self.lock, self.logs)
        self.assertFalse(self.lock.exists())


if __name__ == "__main__":
    unittest.main()
