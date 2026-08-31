# Contributing to GoodCat 股利喵

Human contributors and AI-assisted tools are welcome. Before starting, read
`AGENTS.md`, `docs/COLLABORATION_POLICY.md`, and the relevant product or
calculation contracts. Active AI work and transfers are recorded in
`AI_HANDOFF.md`.

## Standard workflow

1. Create or claim an Issue that defines the problem, scope, acceptance
   criteria, and risk level.
2. Create a single-purpose branch from the current `main`. Do not share a
   writable branch between multiple people or AI agents.
3. Post the claimed scope on the Issue and update `AI_HANDOFF.md` when work is
   transferred.
4. Implement the change with tests and documentation while preserving the
   distinction between ACTUAL, estimated, missing, and formal zero values.
5. Open a Draft PR for early review. Complete the PR template before marking it
   ready for review.
6. After CI and the required human approvals pass, a human maintainer performs
   the squash merge.

## Branch naming

Use lowercase letters, numbers, and hyphens. `<issue>` is the GitHub Issue
number. Documentation initialization without an Issue may use a specific scope.

- `feature/<issue>-<slug>`: new functionality
- `fix/<issue>-<slug>`: bug fix
- `data/<issue>-<slug>`: data source, pipeline, or coverage work
- `docs/<issue-or-scope>-<slug>`: documentation or collaboration policy
- `test/<issue>-<slug>`: test-only work
- `security/<sec-id>-<slug>`: isolated security work
- `chore/<issue-or-scope>-<slug>`: maintenance work
- `ai/<agent>/<type>-<issue>-<slug>`: explicitly identified independent AI workspace

Do not use vague names such as `update`, `test2`, or `ai-fix`. Never push
directly to `main`.

## Commits

Use `<type>: <imperative summary>`. Common types are `feat`, `fix`, `data`,
`docs`, `test`, `security`, and `chore`.

Each commit should be understandable and reversible on its own. Do not include
repository-wide formatting, generated files, personal settings, or unrelated
Issue work.

## Review and merge

- General changes require at least one non-author human approval.
- High-risk changes require one human CODEOWNER approval. High-risk surfaces
  include authentication and authorization,
  security, deployment, database schema or migration, financial and allocation
  calculations, official data sources, and public grading contracts.
- AI review is supplementary evidence and does not count toward the human
  approval requirement.
- All required checks must pass, conversations must be resolved, and the branch
  must be current with its base.
- Squash merge is the default. Merge commits require maintainer approval for a
  meaningful multi-commit history. AI must never merge or force-push.

## Local validation

Run focused tests appropriate to the change. Before opening a PR, run at least:

```powershell
.venv\Scripts\python.exe -m compileall -q backend frontend tests deployment
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
git diff --check
```

If a validation step cannot run, document the reason and residual risk in the
PR.
