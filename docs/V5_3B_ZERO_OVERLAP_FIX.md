# V5-3B zero shared constituent overlap fix

## Decision

Two valid, quality-gated constituent snapshots with no shared disclosed
constituents represent formal zero overlap. Missing, stale or insufficient
snapshots remain unavailable and are not converted to zero.

The pairwise overlap calculation previously summed an empty sequence as Python
integer zero and then called the Decimal-only `quantize()` method. This caused
representative existing-holding allocation requests to raise `AttributeError`
after official constituent snapshots were acquired.

## Change

The empty pairwise sum now starts from `Decimal("0")`, matching the existing
portfolio-weighted overlap implementation. The calculation method, six-decimal
quantization, disclosed weights and quality gates are unchanged.

Deterministic tests cover both layers:

- two fresh snapshots with at least 85% disclosed weight and no common
  constituent return `READY`, `0.000000` and zero shared constituents;
- zero overlap remains available to allocation strategy selection instead of
  being treated as missing overlap.

## Isolated V5-3 replay

Replay date: `2026-09-01`

Candidate database:
`sha256:7def54f0b00338193858746014d3fecb99a18e7bc0d36e1ebebf55844eaefaaa`

- Existing 0050, 10 shares, TWD 100 in months 1/4/7/10:
  `TARGET_MET`, 23 eligible candidates, three plans, five additions and
  TWD 22,822.49 modeled additional capital.
- Existing 00929, 1,000 shares, TWD 3,000 in every month:
  `TARGET_MET`, 34 eligible candidates, three plans, eleven additions and
  TWD 7,489,154.83 modeled additional capital.

The exception is resolved, but the 00929 result remains outside the approved
maximum-five-ETF direction and still depends on Issue #91 paid-versus-announced
dividend semantics. This fix does not complete V5-3 or authorize V4-8.

## Safety boundaries

- No constituent source, snapshot, threshold or missing-data state changes.
- No allocation objective, grade formula, tax rule, API or page changes.
- No production database, deployment, V4-8 or SEC-4 action.
- Human CODEOWNER review remains required because overlap affects allocation.
