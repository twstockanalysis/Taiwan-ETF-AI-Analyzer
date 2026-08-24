# SEC-4 public-host and launch security acceptance

Date: 2026-08-21
Last local rehearsal: 2026-08-24

## Current decision

`NO_GO`

The repository-controlled acceptance implementation is complete, but this
workstation has no registered domain, public host or provider controls. It
cannot truthfully prove public DNS, certificate issuance/renewal, firewall and
administration exposure, shared edge rate limiting, production secret
injection, or off-host backup access. SEC-4 remains an active public-launch
gate. By owner direction on 2026-08-25, local V3 development and page review
may proceed first, but no public launch may occur until one exact deployment
returns `READY`.

## Local production rehearsal evidence

Commit `75722b0b3e2823430bf70e8e9d3716de4dc6e2ac` passed an isolated
Windows 11, WSL 2 and Docker Desktop production-compose rehearsal on
2026-08-24:

- Docker Desktop 4.87.0 used Linux Engine 29.7.2 and Compose 5.4.0;
- the exact backend, frontend and Caddy images built successfully from the
  repository allowlisted contexts;
- the backend and frontend health checks passed behind the Caddy-only
  80/443 exposure;
- HTTPS smoke checks passed for health, frontend availability, anonymous
  private-route denial and correct owner access;
- plain HTTP returned a same-host 308 redirect to HTTPS;
- an isolated copy of `tw_etf-v2-12-20260820.db` passed schema, SQLite
  integrity and foreign-key verification before and after a full three-service
  restart, with every recorded table count preserved; and
- the owner confirmed ETF lookup, dividend composition, holdings cash flow,
  Excel export, private access and refresh persistence in a local browser.

Caddy issued a localhost certificate from its local CA. Its root was supplied
only to the automated smoke process and was not installed into the Windows
trust store. This rehearsal proves local container and application readiness;
it does not satisfy public DNS, publicly trusted TLS or provider-control
evidence and therefore does not change the `NO_GO` decision.

## Automated evidence

`deployment/public_security_acceptance.py` requires explicit network approval,
a clean HTTPS origin, a full 40-character release SHA, a named manual
attestation and an absolute output path outside the repository. It verifies:

- DNS resolves to at least one globally routable address;
- the default trust store accepts the certificate and hostname;
- the negotiated connection is TLS 1.2 or 1.3 and the certificate has at least
  30 days remaining;
- plain HTTP redirects to the same hostname on HTTPS;
- the API and frontend respond and carry the complete Caddy security-header
  contract plus the requested `X-Release-Sha`;
- `/docs`, `/redoc` and `/openapi.json` return 404;
- anonymous and random-token private calls return 401, the correct owner token
  returns 200, and all private response classes are non-cacheable; and
- a body above 64 KiB is rejected at the edge with 413.

The probe refuses redirects for every request. The owner token is read from a
named environment variable, is never accepted on the command line and is not
written to the report. Network failures are reduced to sanitized exception
types in a `NO_GO` result.

## Manual evidence

The external attestation is deliberately not self-certifying. Each section
requires true booleans and a non-placeholder evidence reference for:

1. exact release SHA and matching application/edge containers;
2. public firewall ports and restricted host administration;
3. enabled and tested provider/edge rate limiting;
4. production-secret injection outside Git and launch-value rotation;
5. verified off-host backup plus a passing restore drill; and
6. automatic certificate renewal plus failure alerting.

The reviewer must be named and the review must be timezone-aware and no more
than 24 hours old. The example ships with every boolean false so it cannot be
mistaken for acceptance evidence.

## Decision semantics

`AUTOMATED_READY` means only the external probes passed. Final `READY` requires
both those probes and every fresh manual evidence section to match the same
domain and release SHA. Missing, stale, malformed, mismatched or false evidence
produces `NO_GO` and exit code 1. No exception or limited-approval path exists.

TLS negotiation proves that a strong protocol works, not by itself that every
legacy protocol is disabled. The certificate-renewal evidence should therefore
reference an independent provider or external TLS configuration report. Public
launch also requires the ordinary data-readiness, backup, restart and smoke
gates already documented in `PRODUCTION_DEPLOYMENT.md`.
