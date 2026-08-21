# SEC-3 dependency, container and runtime audit

Date: 2026-08-21

## Decision

The repository-controlled SEC-3 controls are implemented. Promotion still
requires a green `Security gate` workflow for the exact commit. Real DNS, TLS,
host firewall and provider-edge evidence remain the separate SEC-4 launch gate;
they cannot be proven on this workstation because it has no Docker engine or
authorized public host.

## Dependency evidence

- `requirements.lock` pins every direct Python dependency exactly.
- `python -m pip check` reported no broken requirements.
- `pip-audit 2.10.1 -r requirements.lock --strict` resolved the full transitive
  graph against the current advisory service and reported no known
  vulnerabilities on 2026-08-21.
- The application base moved from Python 3.13.7 to the current 3.13.14 slim
  image and the edge moved from Caddy 2.10.2 to 2.11.4 Alpine. The application
  build applies available Debian package security updates before installing
  Python dependencies.
- CI repeats Python auditing and scans both built images with Trivy, failing on
  fixable HIGH or CRITICAL operating-system or library findings.

Advisory data changes over time. A past clean result is not an exception or
allowlist; every pull request and main push reruns the gate.

## Runtime boundary

- Application and edge images use numeric UID 10001 at runtime.
- Root filesystems are read-only. `/tmp` is bounded, `noexec` and `nosuid`.
- All capabilities are dropped from application services. Caddy receives only
  `NET_BIND_SERVICE` for ports 80/443, and every service enables
  `no-new-privileges` and a PID ceiling.
- FastAPI and Streamlit have no published host ports. Only Caddy publishes TCP
  80/443 and UDP 443. The sole host bind mount is the backend database directory
  and it is the only explicitly writable durable mount.
- Source files are installed read-only in the application image and the Docker
  build context remains deny-by-default.

## HTTP boundary

- Caddy rejects bodies above 64 KiB before proxying; FastAPI independently
  enforces the same body ceiling plus target and header ceilings.
- `/docs`, `/redoc` and `/openapi.json` return 404 through the public edge.
- Responses set HSTS, MIME-sniffing, frame, referrer, permissions and a narrow
  frame/base/object CSP policy, while upstream server-identification headers
  are removed.
- Public and owner routes have separate per-source, per-minute process-local
  limits. State is capped at 4,096 source keys to prevent the limiter itself
  from becoming unbounded. Rejections return 429 and `Retry-After`; private
  responses retain `no-store, private`.

The application limiter is a defense-in-depth control for the current single
backend process. SEC-4 must add or verify a shared provider/edge limit before a
multi-replica or publicly advertised launch.

## Automated verification

The GitHub workflow uses immutable action commit SHAs and performs:

1. full-history secret scanning;
2. Python vulnerability and consistency checks;
3. the complete unit/integration regression suite;
4. builds of both application and edge images;
5. numeric non-root UID checks;
6. an isolated backend health probe using read-only root, tmpfs, no added
   capabilities and `no-new-privileges`; and
7. HIGH/CRITICAL Trivy scans of both images.

Local focused runtime/security tests and compilation passed before publication.
The workstation cannot honestly supply local Docker, public TLS, DNS, firewall
or provider-edge results; these are explicit SEC-4 prerequisites.
