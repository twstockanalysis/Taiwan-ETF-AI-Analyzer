"""SEC-4 public-host security acceptance tests."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from deployment.public_security_acceptance import (
    REQUIRED_ATTESTATIONS,
    ROOT,
    _headers_pass,
    _validate_target,
    _write_atomic,
    evaluate_acceptance,
    run_automated_checks,
)


RELEASE_SHA = "a" * 40
EVALUATED_AT = datetime(2026, 8, 21, 8, 0, tzinfo=timezone.utc)


def security_headers() -> dict[str, str]:
    return {
        "strict-transport-security": (
            "max-age=31536000; includeSubDomains"
        ),
        "content-security-policy": (
            "base-uri 'self'; frame-ancestors 'none'; object-src 'none'"
        ),
        "permissions-policy": "camera=(), geolocation=(), microphone=()",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "x-release-sha": RELEASE_SHA,
    }


def complete_attestation() -> dict:
    result = {
        "schema_version": 1,
        "domain": "etf.example.com",
        "release_sha": RELEASE_SHA,
        "reviewed_at": (EVALUATED_AT - timedelta(hours=1)).isoformat(),
        "reviewed_by": "Site owner",
    }
    for section_name, field_names in REQUIRED_ATTESTATIONS.items():
        result[section_name] = {
            **{field_name: True for field_name in field_names},
            "evidence_reference": f"ticket-{section_name}",
        }
    return result


class TestPublicSecurityAcceptance(unittest.TestCase):
    def test_example_attestation_cannot_pass_acceptance(self) -> None:
        attestation = json.loads(
            (ROOT / "deployment" / "public_launch_attestation.example.json")
            .read_text(encoding="utf-8")
        )

        decision = evaluate_acceptance(
            automated={
                "decision": "AUTOMATED_READY",
                "domain": "etf.example.com",
                "release_sha": RELEASE_SHA,
                "checks": [],
            },
            attestation=attestation,
            evaluated_at=EVALUATED_AT,
        )

        self.assertEqual("NO_GO", decision["decision"])

    def test_target_requires_clean_public_https_origin_and_full_sha(self) -> None:
        self.assertEqual(
            ("etf.example.com", RELEASE_SHA),
            _validate_target("https://ETF.EXAMPLE.COM/", RELEASE_SHA),
        )
        for url in (
            "http://etf.example.com",
            "https://127.0.0.1",
            "https://localhost",
            "https://etf.example.com/path",
            "https://etf.example.com:8443",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _validate_target(url, RELEASE_SHA)
        with self.assertRaises(ValueError):
            _validate_target("https://etf.example.com", "abc123")

    def test_header_contract_rejects_missing_or_exposed_headers(self) -> None:
        passed, missing = _headers_pass(security_headers())
        self.assertTrue(passed)
        self.assertEqual([], missing)

        exposed = {**security_headers(), "server": "edge"}
        passed, missing = _headers_pass(exposed)
        self.assertFalse(passed)
        self.assertIn("exposed:server", missing)

    @patch("deployment.public_security_acceptance._http_request")
    @patch("deployment.public_security_acceptance._inspect_tls")
    @patch("deployment.public_security_acceptance._resolve_public_addresses")
    def test_automated_probe_covers_public_and_owner_boundaries(
        self,
        resolve_addresses,
        inspect_tls,
        http_request,
    ) -> None:
        resolve_addresses.return_value = ["1.1.1.1"]
        inspect_tls.return_value = {
            "version": "TLSv1.3",
            "cipher": "TLS_AES_256_GCM_SHA384",
            "expires_at": EVALUATED_AT + timedelta(days=60),
            "issuer": "organizationName=Example CA",
            "subject": "commonName=etf.example.com",
        }
        public_headers = security_headers()
        private_headers = {
            **public_headers,
            "cache-control": "no-store, private",
            "pragma": "no-cache",
        }
        http_request.side_effect = [
            (308, b"", {"location": "https://etf.example.com/"}),
            (200, b'{"status":"healthy"}', public_headers),
            (200, b"html", public_headers),
            (404, b"", public_headers),
            (404, b"", public_headers),
            (404, b"", public_headers),
            (401, b"", private_headers),
            (401, b"", private_headers),
            (200, b"{}", private_headers),
            (413, b"", public_headers),
        ]

        result = run_automated_checks(
            "https://etf.example.com",
            RELEASE_SHA,
            "x" * 32,
            evaluated_at=EVALUATED_AT,
        )

        self.assertEqual("AUTOMATED_READY", result["decision"])
        self.assertTrue(all(item["passed"] for item in result["checks"]))
        self.assertEqual(10, http_request.call_count)
        self.assertNotIn("x" * 32, json.dumps(result))

    def test_complete_current_attestation_produces_ready(self) -> None:
        automated = {
            "decision": "AUTOMATED_READY",
            "domain": "etf.example.com",
            "release_sha": RELEASE_SHA,
        }
        result = evaluate_acceptance(
            automated,
            complete_attestation(),
            evaluated_at=EVALUATED_AT,
        )
        self.assertEqual("READY", result["decision"])
        self.assertEqual(0, result["exit_code"])

    def test_missing_manual_evidence_or_release_mismatch_is_no_go(self) -> None:
        automated = {
            "decision": "AUTOMATED_READY",
            "domain": "etf.example.com",
            "release_sha": RELEASE_SHA,
        }
        attestation = complete_attestation()
        attestation["release_sha"] = "b" * 40
        attestation["firewall"]["only_expected_public_ports"] = False

        result = evaluate_acceptance(
            automated,
            attestation,
            evaluated_at=EVALUATED_AT,
        )

        self.assertEqual("NO_GO", result["decision"])
        failed = {
            item["name"]
            for item in result["acceptance_checks"]
            if not item["passed"]
        }
        self.assertIn("attestation_release", failed)
        self.assertIn("attestation_firewall", failed)

    def test_report_output_is_atomic_and_outside_release_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve() / "security.json"
            _write_atomic(output, '{"decision":"NO_GO"}')
            self.assertEqual(
                {"decision": "NO_GO"},
                json.loads(output.read_text(encoding="utf-8")),
            )
        with self.assertRaises(ValueError):
            _write_atomic(ROOT / "security.json", "{}")


if __name__ == "__main__":
    unittest.main()
