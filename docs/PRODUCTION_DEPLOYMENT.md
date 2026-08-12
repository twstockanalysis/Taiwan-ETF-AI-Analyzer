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
`tw_etf.db`; on Linux ensure container UID 10001 can write it.

## Release sequence

1. Create and verify a backup using `docs/DEPLOYMENT_DATABASE.md`.
2. Rehearse migration on a copy, stop writers, then initialize the durable DB.
3. Run `docker compose --env-file deployment/.env -f deployment/compose.yaml config`.
4. Build with `docker compose --env-file deployment/.env -f deployment/compose.yaml build --pull`.
5. Start with `docker compose --env-file deployment/.env -f deployment/compose.yaml up -d`.
6. Require all three services to become healthy.
7. Run `python deployment/smoke_test.py --base-url https://DOMAIN --owner-token TOKEN`.
8. Restart the stack and repeat the smoke test; confirm the same DB row counts.
9. Enable the M12-3 scheduler only after the release and restore evidence pass.

Rollback means stop writers, preserve the failed DB, deploy the prior image,
restore to a new verified path if schema/data rollback is required, update the
mount, and repeat smoke tests. Never downgrade against a newer live DB without
a rehearsed compatible restore.

## External work still required

Repository validation cannot create a paid host, change DNS, open firewalls or
prove public certificate issuance without owner authorization and credentials.
Record the chosen host, domain, deployment SHA, DNS result, certificate issuer,
smoke output, restart evidence and rollback owner before declaring M12-5
operationally complete.
