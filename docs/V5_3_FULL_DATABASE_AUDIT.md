# V5-3 full-database and planner readiness audit

## Decision

The refreshed database can produce an explicit result state for every audited
request, but it is not yet sufficient for the approved V5 allocation work.
Zero-holding requests can reach their modeled cash target, while every request
with an existing holding loses all eligible additions because portfolio
constituent-overlap evidence is unavailable. The current all-month result also
requires thirteen added ETFs and more than TWD 4.15 million, so data acquisition
alone cannot satisfy the approved maximum-five-ETF result contract.

This is an audit result, not a launch-data decision. V4-8, deployment and SEC-4
remain paused.

## Reproducible evidence

- Code base used to build the candidate: `main@d4cc17c`
- Evaluation date: `2026-09-01`
- Source database SHA-256:
  `6a817e10ff4daeb09c9612490b3ff624a523780d46e3dc629210e80084712a76`
- Candidate database SHA-256:
  `6e245b0bd79d43a19bc38dee4e7f6e4672a5a2140e6ffd15087ea00f19349e95`
- Candidate size: `13,406,208` bytes
- SQLite integrity: `ok`
- Foreign-key violations: `0`
- Official master: 271 raw records, 263 accepted ETFs and 8 explicit
  out-of-scope rejections
- Local candidate and source artifacts:
  git-ignored `reports/v5-3-20260901/`

The source database was not overwritten. The candidate was produced through
`deployment.detail_data_candidate`, then checked through
`deployment.v5_full_database_audit`.

## Full-database coverage

Identity, classification and listing dates are available for 263 of 263 ETFs.
Official daily close history is available for 231 ETFs. Price-return coverage
is 230 for 1M, 223 for 3M, 210 for 6M and 191 for 1Y; the remaining observations
are unavailable primarily because listed history is insufficient.

Dividend history is available for 121 ETFs, calculable yield for 113 and a
complete eFortune estimated component mix for 106. Formal reviewed ACTUAL
components and formal `76W` remain only one event among 1,523 dividend events.
There are 3,044 ACTUAL review-queue records. These figures must not be described
as a complete formal tax-composition database.

Fund size, total expense ratio, distribution period and stock-dividend fields
remain unavailable for all 263 ETFs because a verified source or schema
contract has not been accepted. They remain unavailable rather than zero.

The yield refresh calculated 345 of 1,235 pending events and retained 890
failures. Most failures are TWSE redirect or maximum-redirect responses. A
repeatable checkpoint and retry mechanism is required before this source can be
maintained as a complete routine refresh.

## Planner matrix

The zero-holding 1/4/7/10-month TWD 100 request reaches the modeled target with
47 eligible ETFs, seven additions and TWD 23,556.61 additional capital. The
seven additions exceed the owner-approved V5 maximum of five.

The zero-holding all-month TWD 3,000 request also reports `TARGET_MET`, but
uses thirteen additions and TWD 4,156,803.91. Only the `RECOMMENDED` strategy
is available. This result is mechanically explicit but does not meet the V5-4
portfolio-size or result-variety direction.

The 0050 holding, 0050 plus 00878 holdings, 00929 holding, unsupported-product
holding and missing-price holding cases all return explicit states. Every
otherwise supported existing-holding request has zero eligible additions
because `HOLDING_OVERLAP_UNAVAILABLE` excludes 198 candidates. This is the
highest-priority V5-3 data blocker.

The formal-zero target returns `TARGET_MET` with no additions and zero
additional capital. The missing-reference-price and unsupported-product cases
return `UNAVAILABLE`; missing facts are not converted to formal zero.

## 00929 evidence semantics

`etf_master.is_active = 0` means 00929 is a passive rather than actively
managed ETF. It does not mean the product is inactive or delisted.

As of 2026-09-01 the candidate contains 37 00929 payments whose payment date is
on or before the evaluation date. The latest paid event is TWD 0.38 on
2026-08-14. It also contains one scheduled TWD 0.38 payment dated 2026-09-14.
The current monthly-income repository selects that future date as its
`as_of_date`, causing `FUTURE_DIVIDEND_DATA` and
`FUTURE_DIVIDEND_COMPONENTS` exclusions.

Paid historical evidence and future scheduled sensitivity evidence therefore
need separate data projections. The scheduled event must remain visible in the
detail evidence, but it must not become paid historical cash flow for an
evaluation dated 2026-09-01.

## Data blockers versus V5-4 algorithm blockers

V5-3 data work should proceed in this order:

1. acquire and reconcile official constituent snapshots so zero-to-N existing
   holdings do not remove the entire otherwise supported universe;
2. separate paid history from future scheduled payment evidence throughout the
   calculation-data projection, using 00929 as the acceptance case;
3. make full-market price and yield refreshes checkpointed and resumable, then
   resolve the measured redirect failures without suppressing rejected rows;
4. reduce stale, missing after-tax cash and incomplete component exclusions
   while preserving ACTUAL versus estimated semantics; and
5. add fund size, expense ratio, distribution period or stock dividend only
   after a verified official source and field contract exist.

V5-4 remains responsible for the independent algorithm findings:

- solve with no more than five added ETFs;
- solve zero-to-N holdings rather than rejecting the entire market;
- compare complete whole-share combinations before calculating planning grade;
- return two or three materially distinct non-dominated plans when they exist;
- avoid treating additional capital as a benefit; and
- replace the current bounded best-effort, one-plan result only after
  deterministic replay and owner acceptance.

## Reproduction

```powershell
python -m deployment.detail_data_candidate `
  --source <source.db> `
  --database <new-candidate.db> `
  --artifacts <new-artifact-directory> `
  --evaluated-on 2026-09-01 `
  --allow-network

python -m deployment.v5_full_database_audit `
  --database <candidate.db> `
  --evaluated-on 2026-09-01 `
  --output <new-audit.json>
```

The full JSON evidence records every exclusion code, exact request, result
snapshot, whole-share addition, capital amount, selected-month cash flow,
shortfall, strategy issue and 00929 paid/future event split.
