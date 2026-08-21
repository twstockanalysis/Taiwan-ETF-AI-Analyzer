"""Adversarial SEC-2 authentication and API boundary tests."""

import os
from pathlib import Path
import secrets
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_database_path
from backend.app.api.owner_access import OWNER_TOKEN_ENV
from backend.app.database.connection import get_connection
from backend.app.database.init_db import initialize_database
from backend.app.main import create_app
from backend.app.security import InMemoryRateLimiter


class TestSecurityAPIBoundaries(unittest.TestCase):
    OWNER_TOKEN = "correct-owner-token-with-32-bytes!!"

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_directory.name) / "security.db"
        initialize_database(self.database)
        self.application = create_app()
        self.application.dependency_overrides[get_database_path] = (
            lambda: self.database
        )
        self.client = TestClient(self.application)
        self.environment = patch.dict(
            os.environ,
            {OWNER_TOKEN_ENV: self.OWNER_TOKEN},
            clear=True,
        )
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()
        self.client.close()
        self.application.dependency_overrides.clear()
        self.temp_directory.cleanup()

    def assert_private_no_store(self, response) -> None:
        self.assertEqual("no-store, private", response.headers["cache-control"])
        self.assertEqual("no-cache", response.headers["pragma"])
        self.assertIn("X-Owner-Token", response.headers["vary"])

    def test_every_private_method_rejects_anonymous_direct_access(self) -> None:
        requests = (
            ("GET", "/api/v1/decision-profile", None),
            ("GET", "/api/v1/decision-profile/current-holding-analysis", None),
            ("GET", "/api/v1/decision-profile/decision-records", None),
            ("GET", "/api/v1/decision-profile/decision-records/1", None),
            ("GET", "/api/v1/decision-profile/decision-records/1/export.xlsx", None),
            ("POST", "/api/v1/decision-profile/candidate-analysis/0050", {}),
            (
                "POST",
                "/api/v1/decision-profile/candidate-analysis/0050/decision-records",
                {},
            ),
            ("PUT", "/api/v1/decision-profile/conditions", {}),
            ("PUT", "/api/v1/decision-profile/holdings", {}),
            ("PUT", "/api/v1/decision-profile/holdings/0050", {}),
            ("DELETE", "/api/v1/decision-profile/holdings/0050", None),
        )
        for method, path, payload in requests:
            response = self.client.request(method, path, json=payload)
            with self.subTest(method=method, path=path):
                self.assertEqual(401, response.status_code)
                self.assertNotIn(self.OWNER_TOKEN, response.text)
                self.assert_private_no_store(response)

    def test_private_route_inventory_cannot_expand_without_security_review(self) -> None:
        actual: set[tuple[str, str]] = set()
        visited: set[int] = set()

        def collect(container) -> None:
            if id(container) in visited:
                return
            visited.add(id(container))
            for route in getattr(container, "routes", ()):
                path = str(getattr(route, "path", ""))
                if path.startswith("/api/v1/decision-profile"):
                    actual.update(
                        (method, path)
                        for method in (getattr(route, "methods", None) or set())
                    )
                nested = getattr(route, "original_router", None)
                if nested is not None:
                    collect(nested)

        collect(self.application)
        expected = {
            ("GET", "/api/v1/decision-profile"),
            ("GET", "/api/v1/decision-profile/current-holding-analysis"),
            ("GET", "/api/v1/decision-profile/decision-records"),
            ("GET", "/api/v1/decision-profile/decision-records/{record_id}"),
            (
                "GET",
                "/api/v1/decision-profile/decision-records/{record_id}/export.xlsx",
            ),
            (
                "POST",
                "/api/v1/decision-profile/candidate-analysis/{etf_code}",
            ),
            (
                "POST",
                "/api/v1/decision-profile/candidate-analysis/{etf_code}/decision-records",
            ),
            ("PUT", "/api/v1/decision-profile/conditions"),
            ("PUT", "/api/v1/decision-profile/holdings"),
            ("PUT", "/api/v1/decision-profile/holdings/{etf_code}"),
            ("DELETE", "/api/v1/decision-profile/holdings/{etf_code}"),
        }

        self.assertEqual(expected, actual)

    def test_successful_private_response_is_not_cacheable(self) -> None:
        response = self.client.get(
            "/api/v1/decision-profile",
            headers={"X-Owner-Token": self.OWNER_TOKEN},
        )

        self.assertEqual(200, response.status_code)
        self.assert_private_no_store(response)

    def test_owner_comparison_uses_equal_length_digests(self) -> None:
        with patch(
            "backend.app.api.owner_access.secrets.compare_digest",
            wraps=secrets.compare_digest,
        ) as compare_digest:
            response = self.client.get(
                "/api/v1/decision-profile",
                headers={"X-Owner-Token": "wrong"},
            )

        self.assertEqual(401, response.status_code)
        left, right = compare_digest.call_args.args
        self.assertIsInstance(left, bytes)
        self.assertIsInstance(right, bytes)
        self.assertEqual(32, len(left))
        self.assertEqual(32, len(right))

    def test_oversized_owner_header_fails_without_reflection(self) -> None:
        candidate = "x" * 257
        response = self.client.get(
            "/api/v1/decision-profile",
            headers={"X-Owner-Token": candidate},
        )

        self.assertEqual(401, response.status_code)
        self.assertNotIn(candidate, response.text)
        self.assert_private_no_store(response)

    def test_request_body_header_and_target_limits_fail_closed(self) -> None:
        oversized_body = self.client.post(
            "/api/v1/etfs/0050/target-analysis",
            content=b"x" * (64 * 1024 + 1),
            headers={"Content-Type": "application/json"},
        )
        oversized_header = self.client.get(
            "/health",
            headers={"X-Filler": "x" * (32 * 1024 + 1)},
        )
        oversized_target = self.client.get(
            f"/health?value={'x' * (8 * 1024 + 1)}"
        )

        self.assertEqual(413, oversized_body.status_code)
        self.assertEqual(431, oversized_header.status_code)
        self.assertEqual(414, oversized_target.status_code)
        for response in (oversized_body, oversized_header, oversized_target):
            self.assertNotIn("x" * 100, response.text)

    def test_streamed_body_without_content_length_is_still_bounded(self) -> None:
        def chunks():
            yield b"x" * (32 * 1024)
            yield b"x" * (32 * 1024)
            yield b"x"

        response = self.client.post(
            "/api/v1/etfs/0050/target-analysis",
            content=chunks(),
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(413, response.status_code)
        self.assertNotIn("x" * 100, response.text)

    def test_cross_origin_preflight_cannot_enable_owner_header(self) -> None:
        response = self.client.options(
            "/api/v1/decision-profile",
            headers={
                "Origin": "https://attacker.invalid",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Owner-Token",
            },
        )

        self.assertNotIn("access-control-allow-origin", response.headers)
        self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_public_and_private_rate_limits_are_independent(self) -> None:
        application = create_app(
            public_rate_limit=2,
            private_rate_limit=1,
        )
        application.dependency_overrides[get_database_path] = (
            lambda: self.database
        )
        with TestClient(application) as client:
            first_public = client.get("/health")
            second_public = client.get("/health")
            limited_public = client.get("/health")
            first_private = client.get("/api/v1/decision-profile")
            limited_private = client.get("/api/v1/decision-profile")

        self.assertEqual(200, first_public.status_code)
        self.assertEqual(200, second_public.status_code)
        self.assertEqual(429, limited_public.status_code)
        self.assertGreaterEqual(int(limited_public.headers["retry-after"]), 1)
        self.assertEqual(401, first_private.status_code)
        self.assertEqual(429, limited_private.status_code)
        self.assert_private_no_store(limited_private)

    def test_rate_limiter_bounds_client_memory_and_resets_windows(self) -> None:
        limiter = InMemoryRateLimiter(
            limit=1,
            window_seconds=60,
            max_clients=2,
        )

        self.assertEqual((True, 60), limiter.allow("first", now=0))
        self.assertEqual((True, 60), limiter.allow("second", now=0))
        self.assertEqual((True, 60), limiter.allow("third", now=0))
        self.assertEqual(2, len(limiter._windows))
        self.assertEqual((False, 30), limiter.allow("third", now=30))
        self.assertEqual((True, 60), limiter.allow("third", now=60))

    def test_validation_does_not_reflect_injected_or_extreme_input(self) -> None:
        injected = "<script>alert('private-input')</script>"
        response = self.client.post(
            "/api/v1/etfs/0050/target-analysis",
            json={
                "held_units": 1,
                "unit_price": injected,
                "monthly_after_tax_target": "1e999999",
                "analysis_years": 10,
                "history_years": 3,
            },
        )

        self.assertEqual(422, response.status_code)
        self.assertEqual("Invalid request", response.json()["detail"])
        self.assertNotIn(injected, response.text)
        self.assertNotIn("1e999999", response.text)
        self.assertNotIn("input", response.json()["errors"][0])

    def test_holding_batch_has_a_bounded_item_count(self) -> None:
        response = self.client.put(
            "/api/v1/decision-profile/holdings",
            headers={"X-Owner-Token": self.OWNER_TOKEN},
            json={
                "holdings": [
                    {"etf_code": f"{index:06d}", "held_units": 1}
                    for index in range(501)
                ]
            },
        )

        self.assertEqual(422, response.status_code)
        self.assert_private_no_store(response)

    def test_sql_injection_and_path_traversal_do_not_escape_routes(self) -> None:
        connection = get_connection(self.database)
        try:
            before = connection.execute(
                "SELECT COUNT(*) FROM etf_master"
            ).fetchone()[0]
        finally:
            connection.close()

        injection = quote("0050' OR 1=1--", safe="")
        injected = self.client.get(f"/api/v1/etfs/{injection}/latest-close")
        traversed = self.client.get(
            "/api/v1/etfs/%2E%2E%2F%2E%2E%2F.env/latest-close"
        )

        connection = get_connection(self.database)
        try:
            after = connection.execute(
                "SELECT COUNT(*) FROM etf_master"
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(404, injected.status_code)
        self.assertEqual(404, traversed.status_code)
        self.assertEqual(before, after)

    def test_unexpected_errors_do_not_leak_tracebacks_or_paths(self) -> None:
        missing_database = Path(self.temp_directory.name) / "missing.db"
        application = create_app()
        application.dependency_overrides[get_database_path] = (
            lambda: missing_database
        )
        with TestClient(application, raise_server_exceptions=False) as client:
            response = client.get(
                "/api/v1/decision-profile",
                headers={"X-Owner-Token": self.OWNER_TOKEN},
            )

        self.assertEqual(500, response.status_code)
        self.assertEqual({"detail": "Internal server error"}, response.json())
        self.assertNotIn(str(missing_database), response.text)
        self.assertNotIn("Traceback", response.text)
        self.assert_private_no_store(response)


if __name__ == "__main__":
    unittest.main()
