"""Sanitized SEC-1 secret scanner for the worktree and complete Git history.

The scanner never prints matching values. Findings contain only the scope,
rule name, repository-relative location and line number.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True, order=True)
class Finding:
    scope: str
    rule: str
    location: str
    line: int


@dataclass
class ScanResult:
    findings: set[Finding]
    scanned: dict[str, int]
    oversized: list[str]

    @classmethod
    def empty(cls) -> "ScanResult":
        return cls(findings=set(), scanned={}, oversized=[])


SECRET_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "github-token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    ("openai-api-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("stripe-live-key", re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ),
    (
        "url-credentials",
        re.compile(r"https?://[^\s/:@]+:[^\s/@]+@", re.IGNORECASE),
    ),
    (
        "sensitive-url-parameter",
        re.compile(
            r"https?://[^\s]+[?&](?:api[_-]?key|access[_-]?token|token|signature|secret)=[^\s&#]+",
            re.IGNORECASE,
        ),
    ),
    (
        "repeated-owner-token-shape",
        re.compile(r"\b([A-Za-z0-9]{6,})(?:-\1){2,}\b"),
    ),
)

GENERIC_ASSIGNMENT = re.compile(
    r"\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|"
    r"(?:[a-z0-9]+[_-])*owner[_-]?token|password|passwd|private[_-]?key)"
    r"\b\s*[:=]\s*"
    r"[\"']?([A-Za-z0-9_./+!=:@-]{16,})",
    re.IGNORECASE,
)

SAFE_GENERIC_VALUES = {
    "correct-owner-token-with-32-bytes!!",
    "replace-with-at-least-32-random-characters",
    "test-owner-token",
}
SAFE_GENERIC_MARKERS = (
    "placeholder",
    "replace-with",
    "example-only",
    "test-only",
    "dummy-value",
    "fake-secret",
    "change-me",
    "changeme",
)

IGNORED_SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
IGNORED_SENSITIVE_NAMES = {
    ".env",
    "secrets.toml",
    "id_rsa",
    "id_ed25519",
}
IGNORED_SENSITIVE_SUFFIXES = {
    ".bak",
    ".backup",
    ".db",
    ".jks",
    ".key",
    ".log",
    ".orig",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
    ".tmp",
}


def _run_git(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _safe_generic_value(value: str) -> bool:
    lowered = value.lower()
    if lowered in SAFE_GENERIC_VALUES:
        return True
    if any(marker in lowered for marker in SAFE_GENERIC_MARKERS):
        return True
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_]{15,}", value))


def scan_content(data: bytes, *, scope: str, location: str) -> set[Finding]:
    text = data.decode("utf-8", errors="ignore")
    findings: set[Finding] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in SECRET_RULES:
            if pattern.search(line):
                findings.add(Finding(scope, rule, location, line_number))
        for match in GENERIC_ASSIGNMENT.finditer(line):
            if not _safe_generic_value(match.group(1)):
                findings.add(
                    Finding(scope, "generic-secret-assignment", location, line_number)
                )
    return findings


def _scan_path(path: Path, *, scope: str, result: ScanResult) -> None:
    relative = path.relative_to(ROOT).as_posix()
    if scope == "worktree" and _is_sensitive_repository_path(Path(relative)):
        result.findings.add(Finding(scope, "sensitive-filename", relative, 0))
    size = path.stat().st_size
    if size > MAX_BYTES:
        result.oversized.append(f"{scope}:{relative}")
        return
    result.findings.update(
        scan_content(path.read_bytes(), scope=scope, location=relative)
    )
    result.scanned[scope] = result.scanned.get(scope, 0) + 1


def scan_worktree(result: ScanResult) -> None:
    paths = _run_git(
        "ls-files", "--cached", "--others", "--exclude-standard", "-z"
    ).decode("utf-8").split("\0")
    for value in paths:
        if not value:
            continue
        path = ROOT / value
        if path.is_file():
            _scan_path(path, scope="worktree", result=result)


def scan_local_git_config(result: ScanResult) -> None:
    data = _run_git("config", "--local", "--list")
    result.findings.update(
        scan_content(data, scope="git-config", location=".git/config")
    )
    result.scanned["git-config"] = 1


def _is_ignored_candidate(relative: Path) -> bool:
    if any(part in IGNORED_SKIP_PARTS for part in relative.parts):
        return False
    lowered_parts = {part.lower() for part in relative.parts}
    name = relative.name.lower()
    if name in IGNORED_SENSITIVE_NAMES or name.startswith(".env."):
        return True
    if relative.suffix.lower() in IGNORED_SENSITIVE_SUFFIXES:
        return True
    return bool(lowered_parts & {"backup", "backups", "legacy", "log", "logs", "report", "reports"})


def _is_sensitive_repository_path(relative: Path) -> bool:
    name = relative.name.lower()
    if name == ".env" or (name.startswith(".env.") and not name.endswith(".example")):
        return True
    if name in {"secrets.toml", "id_rsa", "id_ed25519"}:
        return True
    return relative.suffix.lower() in IGNORED_SENSITIVE_SUFFIXES


def scan_ignored(result: ScanResult) -> None:
    paths = _run_git(
        "ls-files", "--others", "--ignored", "--exclude-standard", "-z"
    ).decode("utf-8").split("\0")
    for value in paths:
        if not value:
            continue
        relative = Path(value)
        path = ROOT / relative
        if path.is_file() and _is_ignored_candidate(relative):
            _scan_path(path, scope="ignored", result=result)


def _history_objects() -> list[tuple[str, str]]:
    output = _run_git("rev-list", "--objects", "--all").decode(
        "utf-8", errors="surrogateescape"
    )
    objects: dict[str, str] = {}
    for line in output.splitlines():
        object_id, separator, path = line.partition(" ")
        if separator and object_id not in objects:
            objects[object_id] = path
    unreachable = _run_git("fsck", "--full", "--unreachable", "--no-reflogs").decode(
        "utf-8", errors="replace"
    )
    for line in unreachable.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == "unreachable" and parts[1] == "blob":
            objects.setdefault(parts[2], "[unreachable-blob]")
    return list(objects.items())


def scan_history(result: ScanResult) -> None:
    objects = _history_objects()
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    try:
        for object_id, path in objects:
            process.stdin.write(f"{object_id}\n".encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii", errors="replace").strip()
            parts = header.split()
            if len(parts) != 3:
                continue
            size = int(parts[2])
            if parts[1] != "blob":
                process.stdout.read(size)
                process.stdout.read(1)
                continue
            if size > MAX_BYTES:
                result.oversized.append(f"history:{object_id[:12]}:{path}")
                process.stdout.read(size + 1)
                continue
            data = process.stdout.read(size)
            process.stdout.read(1)
            location = f"{object_id[:12]}:{path}"
            if _is_sensitive_repository_path(Path(path)):
                result.findings.add(
                    Finding("history", "sensitive-filename", location, 0)
                )
            result.findings.update(
                scan_content(data, scope="history", location=location)
            )
            result.scanned["history"] = result.scanned.get("history", 0) + 1
    finally:
        process.stdin.close()
        process.wait(timeout=10)
    _scan_commit_messages(result)


def _scan_commit_messages(result: ScanResult) -> None:
    output = _run_git("log", "--all", "--format=%H%x00%B%x00").decode(
        "utf-8", errors="replace"
    )
    parts = output.split("\0")
    for index in range(0, len(parts) - 1, 2):
        commit_id = parts[index].strip()
        message = parts[index + 1]
        if not commit_id:
            continue
        result.findings.update(
            scan_content(
                message.encode("utf-8"),
                scope="history",
                location=f"{commit_id[:12]}:[commit-message]",
            )
        )
        result.scanned["history"] = result.scanned.get("history", 0) + 1


def run_scan(*, include_ignored: bool, include_history: bool) -> ScanResult:
    result = ScanResult.empty()
    scan_worktree(result)
    scan_local_git_config(result)
    if include_ignored:
        scan_ignored(result)
    if include_history:
        scan_history(result)
    return result


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-ignored", action="store_true")
    parser.add_argument("--include-history", action="store_true")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_scan(
        include_ignored=args.include_ignored,
        include_history=args.include_history,
    )
    print("SEC-1 sanitized secret scan")
    for scope in ("worktree", "git-config", "ignored", "history"):
        if scope in result.scanned:
            print(f"{scope}_items_scanned={result.scanned[scope]}")
    print(f"findings={len(result.findings)}")
    for finding in sorted(result.findings):
        print(
            f"FINDING scope={finding.scope} rule={finding.rule} "
            f"location={finding.location}:{finding.line}"
        )
    print(f"oversized_unscanned={len(result.oversized)}")
    for location in sorted(result.oversized):
        print(f"UNSCANNED location={location}")
    if result.oversized:
        return 2
    return 1 if result.findings else 0


if __name__ == "__main__":
    sys.exit(main())
