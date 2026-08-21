# SEC-2 authentication and API boundary audit

## Decision

`SEC-2` passed on 2026-08-21 after closing four application-layer gaps:
private responses are now non-cacheable, owner-token comparison uses fixed-size
digests, frontend requests no longer follow redirects, and request resources
have explicit application limits. Adversarial tests found no owner-route bypass,
SQL mutation, file traversal, cross-origin owner-header grant, reflected
validation input or exception-detail disclosure after the fixes.

This decision covers authentication and API application boundaries. Dependency,
container, reverse-proxy, TLS, rate-limit, firewall and host hardening remain the
separate `SEC-3` gate.

## Authentication and private-data evidence

- All 11 methods under `/api/v1/decision-profile` inherit the router-level owner
  dependency. A recursive route-inventory test fails if that set changes without
  an explicit security review.
- Anonymous direct requests to every profile, holding, analysis, record and Excel
  export operation return HTTP 401 before request-specific processing.
- Missing or invalid server configuration remains fail-closed with HTTP 503.
- Submitted and configured tokens are SHA-256 digested before constant-time
  comparison, so the comparison operands are always 32 bytes. Submitted tokens
  longer than 256 characters are rejected without reflection.
- Every private success or error response carries `Cache-Control: no-store,
  private`, `Pragma: no-cache` and `Vary: X-Owner-Token`.
- The frontend retains the owner token only in Streamlit session state, does not
  use shared Streamlit caching for private calls, and refuses HTTP redirects so
  `X-Owner-Token` cannot be forwarded to a redirect target.
- No CORS middleware grants an external origin permission to send the owner
  header; an attacker-origin preflight receives no allow-origin or
  allow-credentials header.

## Input and abuse boundaries

The application now rejects:

| Boundary | Limit | Response |
|---|---:|---:|
| Request target, including query | 8 KiB | 414 |
| Total request headers | 32 KiB | 431 |
| Request body | 64 KiB | 413 |
| Manual holding batch | 500 rows | 422 |
| Owner token submitted to the application | 256 characters | 401 |

The body limit is enforced both from `Content-Length` and while reading a
streamed body without that header. Conflicting or invalid content lengths fail
with HTTP 400. Money and unit inputs used by calculations have explicit digit,
precision and quantity limits so compact exponent notation cannot create an
unbounded arithmetic workload.

Request-validation responses expose only stable error type and field location;
they do not include the submitted value. Unexpected exceptions return one
generic JSON message without traceback, exception text or local filesystem
paths. FastAPI remains explicitly configured with `debug=false`.

ETF and record repositories use parameterized SQLite statements. Adversarial
ETF path input containing SQL syntax returned 404 without changing table rows.
Encoded traversal input did not escape the API route or read a local file.

## Verification

- `.venv\Scripts\python.exe -m unittest discover -s tests` passed all 865 tests.
- The 15 focused SEC-2 tests cover authentication, private caching, route
  inventory, direct export access, digest comparison, CORS, redirects, request
  sizes, streamed bodies, bounded batches, validation reflection, injection,
  traversal and unexpected errors.
- Existing owner, decision-profile, calculation, frontend and deployment tests
  remain green.

## Limits

- The in-process limits protect application parsing and calculation resources;
  connection concurrency, request rates and slow-client timeouts require the
  reverse proxy and host controls reviewed in `SEC-3`.
- This workstation still has no Docker installation or public domain, so the
  behavior was verified with isolated FastAPI TestClient requests rather than a
  deployed Caddy/TLS stack.
- The owner gate remains a single-site-owner secret, not a multi-user account,
  password, role or session-management system.

## Next gate

Proceed to `SEC-3` for dependency vulnerabilities, container contents and user,
filesystem permissions, Caddy security headers and HTTPS behavior, rate limits,
firewall exposure, least-privilege mounts, and isolated deployment checks.
