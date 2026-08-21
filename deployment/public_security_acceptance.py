"""Evaluate the public-host SEC-4 security acceptance gate."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import socket
import ssl
import tempfile
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


REPORT_SCHEMA_VERSION = 1
ATTESTATION_SCHEMA_VERSION = 1
MAX_ATTESTATION_BYTES = 64 * 1024
MIN_CERTIFICATE_VALIDITY = timedelta(days=30)
MAX_ATTESTATION_AGE = timedelta(hours=24)
ROOT = Path(__file__).resolve().parents[1]
RELEASE_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_ATTESTATIONS = {
    "deployment": ("release_sha_verified", "containers_match_release"),
    "firewall": (
        "only_expected_public_ports",
        "admin_access_restricted",
    ),
    "provider_edge_rate_limit": ("enabled", "tested"),
    "production_secret": (
        "injected_outside_repository",
        "launch_value_rotated",
    ),
    "backup": ("off_host_copy_verified", "restore_drill_passed"),
    "certificate_renewal": ("configured", "failure_alert_configured"),
}


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        del request, file_pointer, code, message, headers, new_url
        return None


def _http_request(
    url: str,
    *,
    token: str | None = None,
    data: bytes | None = None,
    content_type: str | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    headers: dict[str, str] = {}
    if token:
        headers["X-Owner-Token"] = token
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, headers=headers, data=data)
    opener = urllib.request.build_opener(_NoRedirectHandler)
    try:
        with opener.open(request, timeout=15) as response:
            return (
                response.status,
                response.read(),
                {key.lower(): value for key, value in response.headers.items()},
            )
    except urllib.error.HTTPError as error:
        return (
            error.code,
            error.read(),
            {key.lower(): value for key, value in error.headers.items()},
        )


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def _flatten_certificate_name(value: Any) -> str:
    parts: list[str] = []
    for group in value or ():
        for key, item in group:
            parts.append(f"{key}={item}")
    return ", ".join(parts)


def _validate_target(base_url: str, release_sha: str) -> tuple[str, str]:
    parsed = urllib.parse.urlsplit(base_url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or parsed.port not in {None, 443}
    ):
        raise ValueError("base URL must be a clean HTTPS origin on port 443")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"}:
        raise ValueError("SEC-4 requires a real public hostname")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError("SEC-4 requires a DNS hostname, not an IP address")
    normalized_sha = release_sha.strip().lower()
    if not RELEASE_SHA_PATTERN.fullmatch(normalized_sha):
        raise ValueError("release SHA must contain exactly 40 lowercase hex characters")
    return hostname, normalized_sha


def _resolve_public_addresses(hostname: str) -> list[str]:
    addresses = {
        item[4][0]
        for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    }
    return sorted(addresses)


def _inspect_tls(hostname: str) -> dict[str, Any]:
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    with socket.create_connection((hostname, 443), timeout=15) as connection:
        with context.wrap_socket(connection, server_hostname=hostname) as secure:
            certificate = secure.getpeercert()
            cipher = secure.cipher()
            expires_at = datetime.fromtimestamp(
                ssl.cert_time_to_seconds(certificate["notAfter"]),
                tz=timezone.utc,
            )
            return {
                "version": secure.version(),
                "cipher": cipher[0] if cipher else None,
                "expires_at": expires_at,
                "issuer": _flatten_certificate_name(certificate.get("issuer")),
                "subject": _flatten_certificate_name(certificate.get("subject")),
            }


def _headers_pass(headers: dict[str, str]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    hsts = headers.get("strict-transport-security", "").lower()
    if "max-age=31536000" not in hsts or "includesubdomains" not in hsts:
        missing.append("strict-transport-security")
    csp = headers.get("content-security-policy", "").lower()
    for directive in ("base-uri 'self'", "frame-ancestors 'none'", "object-src 'none'"):
        if directive not in csp:
            missing.append(f"content-security-policy:{directive}")
    expected = {
        "permissions-policy": ("camera=()", "geolocation=()", "microphone=()"),
        "x-content-type-options": ("nosniff",),
        "x-frame-options": ("deny",),
        "referrer-policy": ("strict-origin-when-cross-origin",),
    }
    for name, values in expected.items():
        actual = headers.get(name, "").lower()
        if not all(value in actual for value in values):
            missing.append(name)
    for forbidden in ("server", "x-powered-by"):
        if forbidden in headers:
            missing.append(f"exposed:{forbidden}")
    return not missing, missing


def run_automated_checks(
    base_url: str,
    release_sha: str,
    owner_token: str,
    *,
    evaluated_at: datetime | None = None,
) -> dict[str, Any]:
    hostname, normalized_sha = _validate_target(base_url, release_sha)
    evaluated_at = evaluated_at or datetime.now(timezone.utc)
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    base = f"https://{hostname}"
    checks: list[dict[str, Any]] = []

    addresses = _resolve_public_addresses(hostname)
    public_addresses = [
        value for value in addresses if ipaddress.ip_address(value).is_global
    ]
    checks.append(
        _check(
            "dns_public_addresses",
            bool(public_addresses),
            f"{len(public_addresses)} public address(es)",
        )
    )

    tls = _inspect_tls(hostname)
    checks.append(
        _check(
            "tls_version",
            tls["version"] in {"TLSv1.2", "TLSv1.3"},
            str(tls["version"]),
        )
    )
    certificate_validity = tls["expires_at"] - evaluated_at.astimezone(timezone.utc)
    checks.append(
        _check(
            "certificate_validity",
            certificate_validity >= MIN_CERTIFICATE_VALIDITY,
            f"expires {tls['expires_at'].isoformat()}",
        )
    )

    redirect_status, _, redirect_headers = _http_request(f"http://{hostname}/")
    location = redirect_headers.get("location", "")
    parsed_location = urllib.parse.urlsplit(location)
    redirect_ok = (
        redirect_status in {301, 302, 307, 308}
        and parsed_location.scheme == "https"
        and parsed_location.hostname == hostname
        and parsed_location.port in {None, 443}
    )
    checks.append(
        _check(
            "http_to_https_redirect",
            redirect_ok,
            f"status {redirect_status}",
        )
    )

    health_status, health_body, health_headers = _http_request(f"{base}/health")
    try:
        health_payload = json.loads(health_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        health_payload = {}
    checks.append(
        _check(
            "api_health",
            health_status == 200
            and health_payload.get("status") == "healthy",
            f"status {health_status}",
        )
    )

    frontend_status, _, frontend_headers = _http_request(base)
    checks.append(
        _check(
            "frontend_available",
            frontend_status == 200,
            f"status {frontend_status}",
        )
    )
    for name, headers in (
        ("api_security_headers", health_headers),
        ("frontend_security_headers", frontend_headers),
    ):
        passed, missing = _headers_pass(headers)
        checks.append(
            _check(
                name,
                passed,
                "complete" if passed else f"missing {','.join(missing)}",
            )
        )
        checks.append(
            _check(
                name.replace("security_headers", "release_sha"),
                headers.get("x-release-sha", "").lower() == normalized_sha,
                "matches requested deployment SHA",
            )
        )

    for path in ("/docs", "/redoc", "/openapi.json"):
        status_code, _, _ = _http_request(f"{base}{path}")
        checks.append(
            _check(
                f"blocked_{path.lstrip('/').replace('.', '_')}",
                status_code == 404,
                f"status {status_code}",
            )
        )

    private_url = f"{base}/api/v1/decision-profile"
    anonymous_status, _, anonymous_headers = _http_request(private_url)
    checks.append(
        _check(
            "anonymous_private_denied",
            anonymous_status == 401,
            f"status {anonymous_status}",
        )
    )
    wrong_status, _, wrong_headers = _http_request(
        private_url,
        token=secrets.token_urlsafe(32),
    )
    checks.append(
        _check(
            "wrong_token_denied",
            wrong_status == 401,
            f"status {wrong_status}",
        )
    )
    owner_status, _, owner_headers = _http_request(private_url, token=owner_token)
    checks.append(
        _check(
            "owner_private_allowed",
            owner_status == 200,
            f"status {owner_status}",
        )
    )
    private_cache_headers = (anonymous_headers, wrong_headers, owner_headers)
    private_no_store = all(
        "no-store" in headers.get("cache-control", "").lower()
        and headers.get("pragma", "").lower() == "no-cache"
        for headers in private_cache_headers
    )
    checks.append(
        _check(
            "private_responses_not_cacheable",
            private_no_store,
            "three private response classes checked",
        )
    )

    oversized_status, _, _ = _http_request(
        f"{base}/api/v1/etfs/0050/target-analysis",
        data=b"x" * (64 * 1024 + 1),
        content_type="application/json",
    )
    checks.append(
        _check(
            "edge_body_limit",
            oversized_status == 413,
            f"status {oversized_status}",
        )
    )

    passed = all(item["passed"] for item in checks)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "evaluated_at": evaluated_at.isoformat(),
        "domain": hostname,
        "release_sha": normalized_sha,
        "decision": "AUTOMATED_READY" if passed else "NO_GO",
        "dns_addresses": addresses,
        "tls": {
            "version": tls["version"],
            "cipher": tls["cipher"],
            "expires_at": tls["expires_at"].isoformat(),
            "issuer": tls["issuer"],
            "subject": tls["subject"],
        },
        "checks": checks,
    }


def evaluate_acceptance(
    automated: dict[str, Any],
    attestation: dict[str, Any],
    *,
    evaluated_at: datetime | None = None,
) -> dict[str, Any]:
    evaluated_at = evaluated_at or datetime.now(timezone.utc)
    if evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must include a timezone")
    checks = [
        _check(
            "automated_public_probe",
            automated.get("decision") == "AUTOMATED_READY",
            str(automated.get("decision", "missing")),
        ),
        _check(
            "attestation_schema",
            attestation.get("schema_version") == ATTESTATION_SCHEMA_VERSION,
            "schema version checked",
        ),
        _check(
            "attestation_domain",
            attestation.get("domain") == automated.get("domain"),
            "domain matches automated probe",
        ),
        _check(
            "attestation_release",
            attestation.get("release_sha") == automated.get("release_sha"),
            "release SHA matches automated probe",
        ),
    ]

    try:
        reviewed_at = datetime.fromisoformat(str(attestation.get("reviewed_at", "")))
    except ValueError:
        reviewed_at = None
    timely = (
        reviewed_at is not None
        and reviewed_at.tzinfo is not None
        and timedelta(0) <= evaluated_at - reviewed_at <= MAX_ATTESTATION_AGE
    )
    checks.append(
        _check(
            "attestation_freshness",
            timely,
            "review must be timezone-aware and at most 24 hours old",
        )
    )
    reviewer = str(attestation.get("reviewed_by", "")).strip()
    checks.append(
        _check(
            "attestation_reviewer",
            len(reviewer) >= 3 and not reviewer.startswith("replace-with"),
            "named reviewer required",
        )
    )

    for section_name, field_names in REQUIRED_ATTESTATIONS.items():
        section = attestation.get(section_name)
        section = section if isinstance(section, dict) else {}
        fields_pass = all(section.get(field_name) is True for field_name in field_names)
        reference = str(section.get("evidence_reference", "")).strip()
        reference_pass = (
            len(reference) >= 8
            and not reference.startswith("replace-with")
        )
        checks.append(
            _check(
                f"attestation_{section_name}",
                fields_pass and reference_pass,
                "boolean controls and evidence reference required",
            )
        )

    ready = all(item["passed"] for item in checks)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "evaluated_at": evaluated_at.isoformat(),
        "domain": automated.get("domain"),
        "release_sha": automated.get("release_sha"),
        "decision": "READY" if ready else "NO_GO",
        "exit_code": 0 if ready else 1,
        "automated": automated,
        "acceptance_checks": checks,
    }


def _load_attestation(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"attestation does not exist: {path}")
    if path.stat().st_size > MAX_ATTESTATION_BYTES:
        raise ValueError("attestation exceeds 64 KiB")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("attestation root must be an object")
    return value


def _write_atomic(path: Path, payload: str) -> None:
    if not path.is_absolute():
        raise ValueError("output path must be absolute and outside the release tree")
    resolved = path.resolve()
    if resolved == ROOT or resolved.is_relative_to(ROOT):
        raise ValueError("output path must be outside the release tree")
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary_name).replace(path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the SEC-4 public-host security acceptance gate."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--release-sha", required=True)
    parser.add_argument("--attestation", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--owner-token-env", default="TW_ETF_OWNER_TOKEN")
    parser.add_argument("--allow-network", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    if not args.allow_network:
        parser.error("public security acceptance requires --allow-network")
    owner_token = os.environ.get(args.owner_token_env, "")
    if not 32 <= len(owner_token) <= 256:
        parser.error(
            "owner token environment variable must contain 32-256 "
            f"characters: {args.owner_token_env}"
        )
    hostname, normalized_sha = _validate_target(
        args.base_url,
        args.release_sha,
    )
    try:
        automated = run_automated_checks(
            args.base_url,
            args.release_sha,
            owner_token,
        )
    except (OSError, ssl.SSLError, ValueError, json.JSONDecodeError) as error:
        automated = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "domain": hostname,
            "release_sha": normalized_sha,
            "decision": "NO_GO",
            "dns_addresses": [],
            "tls": None,
            "checks": [
                _check(
                    "automated_probe_execution",
                    False,
                    f"failed with {type(error).__name__}",
                )
            ],
        }
    attestation = _load_attestation(args.attestation)
    result = evaluate_acceptance(automated, attestation)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    _write_atomic(args.output, payload)
    print(payload)
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
