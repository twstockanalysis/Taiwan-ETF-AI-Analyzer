# SEC-1 secret exposure and repository history audit

## Decision

`SEC-1` passed on 2026-08-21. No credential-like value, private key, sensitive
URL parameter or sensitive repository filename was found in the current
worktree, selected ignored runtime artifacts, reachable Git history, commit
messages or local unreachable blobs. No credential rotation or history rewrite
is required from the evidence reviewed in this gate.

This result closes secret-exposure review only. Authentication and API abuse
testing remains the separate `SEC-2` gate.

## Scope and method

The sanitized scanner in `deployment/security_secret_scan.py` checks:

- every tracked and untracked non-ignored worktree file;
- local Git configuration, including credential-bearing remote URL patterns;
- ignored databases, backups, reports, logs, source snapshots and secret-file
  candidates while skipping dependency and bytecode caches;
- every unique blob reachable from all local and remote refs;
- every local unreachable blob reported by `git fsck`;
- all 287 reachable commit messages;
- provider token formats, private-key headers, credential-bearing URLs,
  repeated local-owner-token shapes and generic sensitive assignments; and
- sensitive filenames such as `.env`, `secrets.toml`, private keys and SQLite
  databases, even when their contents do not match a token rule.

Findings contain only scope, rule, object or file location and line number. The
matching value is never printed.

## Evidence

The final full scan command was:

```powershell
.venv\Scripts\python.exe deployment\security_secret_scan.py `
  --include-ignored `
  --include-history
```

It reported:

| Scope | Items scanned |
|---|---:|
| Worktree | 410 |
| Local Git configuration | 1 |
| Ignored runtime artifacts | 25 |
| Reachable/unreachable history blobs plus commit messages | 1,508 |
| Findings | 0 |
| Oversized unscanned items | 0 |

The origin fetch specification covers every remote branch. The history scan
therefore includes all currently fetched origin branches rather than only
`main`. The item counts are the 2026-08-21 pre-publication snapshot; local
unreachable-blob counts can change as Git creates or prunes temporary objects.

Direct local HTTP probes covered `.env`, Streamlit secrets, deployment `.env`,
the SQLite database path, reports and logs. FastAPI returned HTTP 404 for all
six paths. Streamlit returned its normal `text/html` application shell for
each unknown path: all responses were the same 10,626-byte HTML response as
the root page, not the requested files.

## Safeguards added

- `.gitignore` now explicitly rejects general environment files, Streamlit
  secrets, key material, logs, reports, backups and source snapshots in
  addition to the existing database and generated-data rules.
- `.dockerignore` denies the repository by default and allowlists only
  `requirements.lock`, `backend/` and `frontend/`, preventing local databases,
  `.env`, Git history, reports and backups from entering the Docker build
  context.
- Static deployment-contract tests verify the Docker context allowlist and
  sensitive ignore rules.
- The production release sequence now requires the full sanitized scan before
  backup, build or deployment.

## Limits

- The scanner is deterministic pattern and filename analysis; it cannot prove
  the absence of a novel credential format that resembles ordinary prose.
- Docker is not installed on this workstation, so the `.dockerignore` contract
  is statically tested but an actual container build-context transfer was not
  observed.
- Credentials stored only in external provider accounts are outside the Git
  repository and must be reviewed through their provider audit logs and
  rotation policy.
- The fixed local owner token used for browser rehearsal remained process-local
  and was not written to source, ignored deployment files, reports or Git.

## Next gate

Proceed to `SEC-2` for owner-token comparison, private caching, direct API and
export boundaries, validation abuse, injection, traversal, redirect, payload,
error-leakage and denial-of-service tests.
