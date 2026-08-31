# Human and multi-AI GitHub collaboration policy

## 1. Purpose

Enable people and multiple AI agents to work in parallel while preserving
single ownership, traceable decisions, financial-data semantics, security
boundaries, and reversible Git history. Issues are the source of requirements,
PRs are the source of review and merge decisions, and `AI_HANDOFF.md` is the
current repository source for unfinished work.

## 2. Roles

- **Maintainer**: manages the repository, branch protection, labels, releases,
  deployments, secrets, and final merges.
- **Human contributor**: claims Issues, implements work, or sponsors AI work and
  remains responsible for requirements and acceptance.
- **Implementer AI**: reads, modifies, tests, and prepares evidence within an
  authorized scope. It cannot expand its own scope or approve itself.
- **Reviewer AI**: performs a read-only review of another implementer's diff and
  reports reproducible issues. It cannot merge or replace human review.
- **Automation**: runs fixed CI and security gates. Only the workflow result
  itself may act as a required check.

Every Issue requires a human sponsor. Without one, AI work is limited to
read-only analysis or a Draft proposal.

## 3. Ownership and parallel work

1. Each Issue has one active implementer. Split large Issues into non-overlapping
   child Issues before parallel implementation.
2. Each implementer uses a separate branch and worktree. Two AI agents must not
   write to the same worktree or share force-push access.
3. The Issue's opening post or a progress comment records the `Claimed scope`,
   including files, modules, and the expected release time.
4. Shared cross-module files, including schemas, API models, navigation, global
   themes, requirements, and migrations, have one active owner at a time. Other
   work waits through dependency Issues or stacked PRs.
5. On detecting overlap, stop writing, preserve local changes, and let the human
   sponsor decide how to split, sequence, or reassign ownership.

## 4. AI authorization matrix

| Level | Allowed actions | Required authorization |
| --- | --- | --- |
| A0 Read | Search, read files, inspect Git or CI state, and propose a plan | An Issue or user request |
| A1 Local implementation | Modify in-scope files, run tests, and produce a local diff | Explicit implementation request |
| A2 Local Git | Create a branch or worktree, stage, and commit | Explicit sponsor authorization or a task that explicitly requires a commit |
| A3 GitHub write | Push, create or update Issues and PRs, comment, and upload attachments | Explicit authorization after confirming the repository and purpose |
| A4 Maintainer operations | Merge, force-push, release, deploy, change branch protection or secrets, and operate on production data | Prohibited for AI; human maintainer only |

No authorization level permits an AI to expose secrets, private data, browsing
history, or unapproved local files. Authorization applies only to the current
task and is never permanently inherited from earlier approval.

## 5. Issue policy

- Describe the problem and user impact before the technical solution.
- Required sections are scope, out of scope, acceptance criteria, data
  semantics, security and privacy risks, dependencies, and AI suitability.
- Mark financial or tax formulas, data sources, schemas, public grading,
  authentication, and deployment Issues as `risk:high`.
- Unconfirmed requirements may create only a `status:needs-decision` Issue; do
  not implement a guessed outcome.

Recommended labels include `type:feature`, `type:bug`, `type:data`, `type:docs`,
`risk:high`, `status:ready`, `status:blocked`, `ai:allowed`, `ai:review-only`, and
`needs-human`.

## 6. Pull request policy

- A PR addresses one primary Issue. Split independently reversible concerns
  into separate PRs.
- Use Draft status while work is in progress. Before marking a PR ready, finish
  the template, synchronize the base, remove untracked artifacts, and attach
  validation evidence.
- Disclose AI participation, including the tool or agent, implementation or
  review role, human sponsor, authorization scope, and areas not manually
  line-reviewed by a human.
- Reviewers judge the diff, tests, and contracts; a PR description is not proof
  that a claim was verified.
- Authors must reply to and resolve important review comments. Do not hide
  unresolved discussion behind a new AI-generated summary.

## 7. Merge policy

Protect `main` with:

- no direct push, force-push, or branch-deletion bypass;
- required pull request, conversation resolution, and status checks;
- required checks covering the existing Security gate regression, secret scan,
  dependency audit, and container security;
- at least one non-author human approval for general PRs and one human
  CODEOWNER approval for high-risk PRs;
- dismissal of stale approvals after new commits; authors cannot approve their
  own PRs, and AI approval does not count;
- squash merge and automatic source-branch deletion by a human maintainer only.

## 8. Handoff and failure recovery

When an AI or person changes, work pauses, or authorization blocks progress,
record the exact branch, base, commit, PR, claimed files, completed and remaining
work, tests, and next step in `AI_HANDOFF.md`. The next implementer must recheck
GitHub and the worktree instead of assuming from chat memory that work was
pushed or merged.

If CI fails, reproduce the smallest failure and determine whether the PR caused
it. Never modify or skip a test merely to obtain a passing result. Return to the
Issue for a human decision before changing a contract or acceptance criterion.

## 9. GoodCat project gates

- Keep ACTUAL, eFortune fallback, `76W`, missing, and formal zero semantics distinct.
- Financial, tax, cash-flow, whole-share allocation, and quality-grade changes
  require deterministic tests and explainable output.
- Official data imports retain source, date, and review basis. AI cannot promote
  an unreviewed source to official status.
- A public release identifies one exact commit. Only a human maintainer may
  declare launch after SEC-4 passes.
- Report vulnerabilities, credentials, authentication bypasses, and suspected
  leaks privately through the Security Advisory process in `SECURITY.md`, not a
  public Issue.

## 10. GitHub configuration checklist

When enabling this policy, a maintainer configures repository settings to:

- protect `main` with the required reviews and checks above;
- enable CODEOWNERS review and stale-approval dismissal;
- prohibit bypass except for a documented emergency maintainer break-glass,
  followed by an Issue and PR;
- enable automatic deletion of merged branches, private vulnerability
  reporting, secret scanning, and Dependabot alerts;
- create the recommended labels because GitHub does not create labels merely
  because an Issue Form references them;
- confirm that GitHub loads the Issue and PR templates from the default branch.
