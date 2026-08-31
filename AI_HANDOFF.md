# AI handoff

This file is the repository handoff point for human and multi-AI work. Read it
before starting. Update it when work pauses, is blocked, or changes implementer.
Move merged or obsolete entries to their Issue or PR so this file contains only
current work.

## Active handoff

- Status: `ACTIVE`
- Issue: `#76` — https://github.com/twstockanalysis/goodcat-website/issues/76
- Owner / human sponsor: `GoodCat owner / current requester`
- Current implementer: `Codex /root`
- Branch: `docs/76-english-collaboration`
- Base branch / commit: `data/74-detail-page-official-data / 0669ba058942f4615040e8dd725bd30da3045c05`
- Latest commit: `N/A — working-tree changes are not committed`
- Pull request: `N/A`
- Last updated: `2026-08-31`

### Objective

Rewrite repository-facing collaboration documentation and templates in English
while preserving the product name `GoodCat 股利喵`, policy meaning, data
semantics, safety boundaries, links, commands, and exact handoff facts. Remove
the duplicated collaboration introduction from README because GitHub already
provides a dedicated Contributing page.

### Claimed scope

- `README.md`
- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/COLLABORATION_POLICY.md`
- `AI_HANDOFF.md`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/*.yml`

Do not modify product UI copy, source-code comments, API messages, historical
acceptance evidence, financial contracts, V5 implementation, deployment,
repository settings, or production data.

### Completed

- Created Issue #76 with the owner-approved documentation scope.
- Created an isolated stacked worktree from the exact PR #75 branch commit so
  the V5-1 website and data-review work remain unchanged.
- Inventoried all collaboration documents, PR templates, and Issue Forms that
  contain Traditional Chinese prose.
- Rewrote README, collaboration rules, contributor guidance, policy, PR
  template, Issue Forms, and this handoff in English.
- Kept `GoodCat 股利喵` as the product name and moved the collaboration entry
  point exclusively to `CONTRIBUTING.md`.
- Updated Issue #76 and PR #75 so their review wording matches the owner's
  one-human approval decision.
- Validated the translated documents, Issue Forms, local links, and whitespace.

### Remaining

- Commit, push, and open a Draft stacked PR against the PR #75 branch.
- After PR #75 merges, retarget and synchronize the documentation PR with
  `main` before human review and merge.

### Validation evidence

- Parsed all 5 Issue template YAML files with PyYAML and validated required
  Issue Form structure and unique field IDs.
- Confirmed all in-scope Markdown prose is English after excluding the literal
  product name `GoodCat 股利喵`.
- Checked local Markdown links in README, AGENTS, CONTRIBUTING, the
  collaboration policy, this handoff, and the PR template; no broken links.
- Searched for obsolete two-human approval wording; no matches.
- `git diff --check` passed.
- Runtime regression was not repeated because this branch changes only
  repository documentation and GitHub templates; PR #75 retains its separate
  1,047-test implementation evidence.

### Decisions and invariants

- All in-scope prose is English except the product name `GoodCat 股利喵`.
- README begins with the project introduction; collaboration instructions live
  in the dedicated Contributing page and collaboration documents.
- The owner changed the approval policy: general PRs require one non-author
  human approval, and high-risk PRs require one human CODEOWNER approval.
  Authorization levels, merge restrictions, data semantics, and SEC-4
  requirements remain unchanged.
- ACTUAL, eFortune estimated fallback, formal `76W`, missing, and formal zero remain
  distinct.

### Risks or blockers

- This is a stacked documentation branch until PR #75 merges.
- Translating policy text can accidentally change meaning; review must compare
  every safety and financial-data invariant with the source wording.

### Next safe action

Validate the English diff and templates, then create a Draft stacked PR. Do not
merge, deploy, change repository settings, or operate on production data.

## Concurrent review

- Issue: `#74` — https://github.com/twstockanalysis/goodcat-website/issues/74
- Draft PR: `#75` — https://github.com/twstockanalysis/goodcat-website/pull/75
- Branch: `data/74-detail-page-official-data`
- Latest implementation commit: `3e35f6b4a985b1102ec70dfe7c5dfff70ecd53c2`
- Latest branch commit: `0669ba058942f4615040e8dd725bd30da3045c05`
- Status: waiting for one human CODEOWNER approval; AI must not merge.
- V4-8, formal deployment, and SEC-4 remain paused through V5-5.

## Update rules

1. Record exact commit SHAs, branches, Issues, and PR links. Do not write
   "latest" or "just now."
2. Distinguish modified, committed, pushed, PR created, and merged states.
3. Record omitted tests and reasons. Never describe focused tests as a full
   regression.
4. List claimed files. A new implementer must verify the worktree and remote
   state before clearing the scope.
5. Never record tokens, accounts, cookies, production data, browsing history,
   or local secrets in this file.
