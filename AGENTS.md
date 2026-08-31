# GoodCat 股利喵 — AI collaboration rules

This file applies to the entire repository. Every AI assistant, agent, and
automation tool must read it before starting work. See
[`docs/COLLABORATION_POLICY.md`](docs/COLLABORATION_POLICY.md) for the complete
policy, and update [`AI_HANDOFF.md`](AI_HANDOFF.md) whenever work is paused or
transferred.

## Product and architecture

GoodCat 股利喵 is a Taiwan ETF cash-flow planning website for ETF beginners.
The architecture is Streamlit frontend → FastAPI backend → service/repository →
SQLite.

- Results must be transparent and explainable, including assumptions, reasons,
  limitations, estimates, risks, and exclusion reasons.
- Do not provide buy or sell instructions, and do not present an ETF quality
  grade as a conclusion about personal suitability.
- Missing formal ACTUAL dividend composition must remain missing. Never treat
  missing data as zero, and never relabel the eFortune estimated realized-capital-
  gain category as formal `76W`.
- SEC-4 remains mandatory before public deployment. No AI may declare a public
  launch or a `READY` decision.

## Before starting work

1. Read the Issue, relevant PRD or contract, `AI_HANDOFF.md`, and current
   `git status`.
2. Verify the branch, base, existing PR, uncommitted changes, and claimed scope.
   Never assume that a previous AI committed, pushed, or merged its work.
3. Use one primary branch and one active implementer per Issue. Concurrent AI
   work must use separate branches and worktrees; never share a writable tree.
4. Identify the files and modules you expect to modify. Stop and coordinate if
   they overlap another active claimed scope.

## AI permissions

- Allowed by default: read files, search, run non-mutating checks, make in-scope
  local changes, and run tests.
- Requires explicit human authorization: create or switch a shared branch,
  commit, push, create or modify an Issue or PR, post external comments, upload
  files, or change GitHub settings.
- AI must never perform: merge, force-push, rewrite another contributor's
  history, delete a remote branch, release, production deployment, SEC-4
  approval, secret or permission changes, or operations on a production
  database or real account.
- AI review does not replace human approval, and an author AI cannot approve
  its own work.
- Never expose, commit, or transmit tokens, cookies, personal data,
  non-anonymized production data, browsing history, or local secrets.

## Implementation and validation

- Preserve existing user and collaborator changes. Never use
  `git reset --hard`, overwrite changes through an arbitrary checkout, or run an
  unconfirmed bulk deletion.
- Calculation, API, and data-semantic changes require corresponding tests and
  contract or API documentation updates.
- Streamlit changes must follow the official guidance for the installed
  version. Do not add deprecated `components.v1`, `use_container_width`, or
  unnecessary HTML/CSS workarounds.
- Run focused tests at minimum. For high-risk work or PR preparation, run:

```powershell
.venv\Scripts\python.exe -m compileall -q backend frontend tests deployment
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

- Before committing, run `git diff --check` and confirm that no secrets,
  databases, logs, temporary files, or unrelated artifacts are included.

## Git and pull requests

- Follow the branch naming rules in `CONTRIBUTING.md`. Never develop or push
  directly on `main`.
- Keep commits small and reversible, using
  `<type>: <imperative summary>`. Do not mix unrelated fixes.
- Every PR must link an Issue and include test, risk, data-semantic, AI
  participation, and handoff evidence. Use a Draft PR while work is in progress.
- `main` accepts changes only through PRs. A human maintainer may squash-merge
  only after CI passes, the branch is current, and at least one non-author human
  approves.
- Security, authentication, deployment, schema or migration, financial or tax
  calculations, and official data-source changes require one human approval,
  and that approver must be a CODEOWNER.

## Handoff

Update `AI_HANDOFF.md` immediately when work is incomplete, transferred, or
waiting on an external decision. Record the objective, branch and commit,
completed and remaining work, tests, known risks, claimed files, and next safe
step. A chat summary alone is not a valid handoff.
