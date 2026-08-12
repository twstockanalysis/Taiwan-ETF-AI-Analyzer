"""Run a declarative sequence of production jobs with a lock and JSON report."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JobResult:
    name: str
    status: str
    exit_code: int
    started_at: str
    completed_at: str


@dataclass(frozen=True)
class ScheduledRunReport:
    status: str
    started_at: str
    completed_at: str
    jobs: list[JobResult]


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_schedule(config_path: str | Path, report_path: str | Path,
                 lock_path: str | Path, log_directory: str | Path) -> ScheduledRunReport:
    """Run configured argv arrays sequentially; stop after the first failure."""

    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    jobs = config.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("排程設定必須包含至少一個 jobs 項目")
    lock = Path(lock_path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeError(f"已有排程正在執行：{lock}") from error
    os.close(descriptor)
    started = datetime.now(timezone.utc)
    results: list[JobResult] = []
    logs = Path(log_directory)
    logs.mkdir(parents=True, exist_ok=True)
    try:
        for index, job in enumerate(jobs, start=1):
            if not isinstance(job, dict) or not isinstance(job.get("argv"), list):
                raise ValueError("每個 job 必須提供 argv 陣列")
            name = str(job.get("name", f"job-{index}"))
            if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
                raise ValueError(f"job 名稱只能包含英數字、底線與連字號：{name}")
            argv = [str(value) for value in job["argv"]]
            if not argv:
                raise ValueError(f"job {name} 的 argv 不得為空")
            job_started = datetime.now(timezone.utc)
            completed = subprocess.run(argv, shell=False, capture_output=True, text=True, check=False)
            job_completed = datetime.now(timezone.utc)
            log_path = logs / f"{started.strftime('%Y%m%dT%H%M%SZ')}-{index:02d}-{name}.log"
            log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
            status = "success" if completed.returncode == 0 else "failed"
            results.append(JobResult(name, status, completed.returncode,
                                     job_started.isoformat(), job_completed.isoformat()))
            if completed.returncode != 0:
                break
        finished = datetime.now(timezone.utc)
        report = ScheduledRunReport(
            "success" if len(results) == len(jobs) and all(item.status == "success" for item in results) else "failed",
            started.isoformat(), finished.isoformat(), results)
        _write_json_atomic(Path(report_path), asdict(report))
        return report
    finally:
        lock.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="M12-3 排程工作執行器")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--log-directory", required=True, type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    report = run_schedule(args.config, args.report, args.lock, args.log_directory)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    if report.status != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
