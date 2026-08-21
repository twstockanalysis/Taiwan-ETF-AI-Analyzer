# Production deployment

M12-5 packages FastAPI and Streamlit behind Caddy. Only Caddy publishes host
ports; application services stay on the Compose network. Caddy obtains and
renews HTTPS certificates when `SITE_DOMAIN` resolves to the host and inbound
TCP 80/443 plus UDP 443 are allowed.

## Host prerequisites

- A Linux or Windows host with Docker Engine and Compose v2
- A domain A/AAAA record pointing at the host
- Independent durable storage and backup storage
- Firewall exposing only 80/443 publicly; SSH/RDP restricted administratively

Copy `deployment/.env.example` to `deployment/.env` outside source control.
Generate `TW_ETF_OWNER_TOKEN` with at least 32 cryptographically random
characters. Set `DATA_DIRECTORY` to the durable directory containing
`tw_etf.db`; on Linux ensure container UID 10001 can write it. Set
`RELEASE_SHA` to the exact 40-character commit deployed by the application and
edge containers. Caddy publishes this non-secret identifier as
`X-Release-Sha` so the external acceptance probe can reject a mismatched host.

The default application limits are 600 public and 120 owner-route requests per
source address per minute. They may be lowered with the two rate-limit values in
`deployment/.env`. This bounded in-process control protects a single backend
process; a future multi-replica deployment must also configure a shared limit
at the hosting provider or edge. Keep FastAPI and Streamlit unpublished and
allow inbound host traffic only to Caddy on TCP 80/443 and UDP 443.

## Release sequence

1. Run `.venv\Scripts\python.exe deployment\security_secret_scan.py --include-ignored --include-history`.
   It must report zero findings and zero unscanned oversized objects without
   printing secret values.
2. Create and verify a backup using `docs/DEPLOYMENT_DATABASE.md`.
3. Rehearse migration on a copy, stop writers, then initialize the durable DB.
4. Run `docker compose --env-file deployment/.env -f deployment/compose.yaml config`.
5. Build with `docker compose --env-file deployment/.env -f deployment/compose.yaml build --pull`.
6. Start with `docker compose --env-file deployment/.env -f deployment/compose.yaml up -d`.
7. Require all three services to become healthy.
8. Confirm `/docs`, `/redoc` and `/openapi.json` return 404 through Caddy and
   plain HTTP redirects to the production HTTPS origin.
9. Export the owner token to `TW_ETF_OWNER_TOKEN`, then run
   `python deployment/smoke_test.py --base-url https://DOMAIN`. The command
   intentionally refuses redirects and never accepts the secret as a command-
   line value.
10. Restart the stack and repeat the smoke test; confirm the same DB row counts.
11. Enable the M12-3 scheduler only after the release and restore evidence pass.

Rollback means stop writers, preserve the failed DB, deploy the prior image,
restore to a new verified path if schema/data rollback is required, update the
mount, and repeat smoke tests. Never downgrade against a newer live DB without
a rehearsed compatible restore.

## External work still required

Repository validation cannot create a paid host, change DNS, open firewalls or
prove public certificate issuance without owner authorization and credentials.
Record the chosen host, domain, deployment SHA, DNS result, certificate issuer,
smoke output, restart evidence and rollback owner before declaring M12-5
operationally complete. Until the SEC-4 command returns `READY` for the exact
deployed SHA, public launch and V3 work remain blocked.

The repository security workflow builds both images, proves their numeric UID,
runs the backend with a read-only root filesystem and dropped capabilities, and
fails on fixable high or critical Trivy findings. A green workflow is required
for this gate, but it cannot replace host firewall, DNS, certificate-renewal or
provider-level rate-limit evidence.

## SEC-4 public-host acceptance

Copy `deployment/public_launch_attestation.example.json` outside the release
tree. Keep every boolean false until its evidence exists. The named reviewer
must record references for the exact release covering:

- deployed commit and matching application/edge containers;
- firewall exposure limited to TCP 80/443 and UDP 443, with SSH/RDP restricted;
- a configured and tested shared provider or edge rate limit;
- production owner-secret injection outside the repository and launch-time
  rotation;
- a verified off-host backup and successful restore drill; and
- automatic certificate renewal plus failure alerting.

Within 24 hours of that review, run the external probe from a network outside
the production host:

```powershell
$deploymentSha = git rev-parse HEAD
.venv\Scripts\python.exe deployment\public_security_acceptance.py `
  --base-url https://DOMAIN `
  --release-sha $deploymentSha `
  --attestation D:\tw-etf-ops\security\launch-attestation.json `
  --output D:\tw-etf-ops\security\launch-acceptance.json `
  --allow-network
```

The owner token is read only from `TW_ETF_OWNER_TOKEN`. The output path is
mandatory, absolute and outside the release tree. The report never records the
token or manual evidence references. It returns exit code 0 only for `READY`.

The automated half verifies public DNS addresses, default trust and hostname
certificate validation, at least 30 days of remaining certificate validity,
TLS 1.2/1.3 negotiation, HTTP-to-HTTPS redirect, frontend/API security headers,
the public release SHA, blocked API docs, owner boundaries, private no-store
headers and the edge body limit. Negotiating a strong TLS version does not by
itself prove that every legacy protocol is disabled; include an independent
provider or external TLS scan in the certificate-renewal evidence.

## Native local rehearsal without Docker

Run FastAPI on `127.0.0.1:8000` and Streamlit on `127.0.0.1:8501` with the
same isolated absolute `TW_ETF_DATABASE_PATH`. Set a local-only
`TW_ETF_OWNER_TOKEN` and point Streamlit at FastAPI with
`TW_ETF_API_URL=http://127.0.0.1:8000`. Then run:

```powershell
.venv\Scripts\python.exe deployment\local_smoke_test.py `
  --owner-token $env:TW_ETF_OWNER_TOKEN
```

This validates both health endpoints, frontend availability, anonymous and
wrong-token denial, and owner access. It does not validate containers, reverse
proxy routing, TLS, DNS, public firewall behavior or certificate renewal.

The 2026-08-12 native rehearsal on this workstation passed all these checks.
It used an isolated migrated copy of the candidate database, preserved all
eight existing-table counts, returned SQLite integrity `ok` and zero foreign-
key violations. A test target of 4,321 TWD remained present after restarting
FastAPI, proving native-process persistence against the isolated file.

The owner then completed the browser acceptance on the same date and confirmed
all five visible behaviors: public ETF pages rendered, the sidebar owner unlock
was present, the test token revealed the private navigation, the persisted
4,321 TWD monthly target was visible, and relocking removed the private entry.
