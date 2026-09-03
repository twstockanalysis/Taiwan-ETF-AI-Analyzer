# V5-3 full-database and planner readiness audit

## Decision

The refreshed database is not yet sufficient for the approved V5 allocation
work. Official constituent acquisition improved the calculation-data gate from
zero to 116 of 157 target ETFs, but two representative existing-holding
requests now raise an allocator exception when a valid pair has zero shared
constituents. A 0050 plus 00878 request remains fail-closed because 00878 is one
of twenty-two Cathay ETFs whose official source is verified but not automated.

Zero-holding requests still reach their modeled cash target. They now return
three strategies, but the quarterly result requires seven added ETFs and the
all-month result requires thirteen plus more than TWD 4.15 million. Data
acquisition alone therefore cannot satisfy the approved maximum-five-ETF
result contract.

This is an audit result, not a launch-data decision. V4-8, deployment and SEC-4
remain paused.

The reproducible audit pass defined by Issue #90 is complete after recording
all 263 ETFs across all 18 required detail fields and all 263 market candidates
for each of eight planner requests. This does not complete the broader V5-3
product phase. V5-3 remains in progress until the accepted data fixes are
applied and representative normal requests produce usable results without an
allocator exception.

## Reproducible evidence

- Code base used to build the candidate: `main@d4cc17c`
- Evaluation date: `2026-09-01`
- Source database SHA-256:
  `6a817e10ff4daeb09c9612490b3ff624a523780d46e3dc629210e80084712a76`
- Candidate before constituent acquisition SHA-256:
  `6e245b0bd79d43a19bc38dee4e7f6e4672a5a2140e6ffd15087ea00f19349e95`
- Candidate after constituent acquisition SHA-256:
  `7def54f0b00338193858746014d3fecb99a18e7bc0d36e1ebebf55844eaefaaa`
- Candidate size after constituent acquisition: `14,151,680` bytes
- SQLite integrity: `ok`
- Foreign-key violations: `0`
- Official master: 271 raw records, 263 accepted ETFs and 8 explicit
  out-of-scope rejections
- Local candidate and source artifacts:
  git-ignored `reports/v5-3-20260901/`
- Consolidated full audit:
  git-ignored `reports/v5-3-20260901/complete-v5-3-audit.json`
  (`2,447,164` bytes)

The source database was not overwritten. The candidate was produced through
`deployment.detail_data_candidate`, enriched through
`backend.app.data_sources.constituent_batch_pipeline`, then checked through
`deployment.v5_full_database_audit`.

The consolidated audit contains 263 per-ETF field records with explicit
`AVAILABLE` or reasoned `UNAVAILABLE` status. Every planner request also keeps
its 263-candidate market evidence, including supported and eligible counts,
component basis, formal 76W availability, holding-overlap status and percentage,
constituent snapshot dates, freshness and all reason codes. Allocation-stage
exceptions retain the successfully completed market-eligibility evidence.

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

## Constituent acquisition findings

The batch plan contains 157 calculation-quality targets across 21 issuers. Of
these, 134 ETFs have automated official-source adapters. Twenty-two Cathay ETFs
and one BlackRock ETF are `SOURCE_NOT_AUTOMATED`, so the theoretical maximum
coverage before adding another adapter is 85.35%, below the 90% gate.

The isolated full batch imported 121 ETFs and 9,049 positions. Thirteen
automated targets failed. The resulting gate is `NO_GO`: 116 of 157 ETFs
(73.885350%) and 18 of 21 issuers (85.714286%) pass freshness and disclosed
weight checks. Five imported Capital snapshots are future-dated relative to
the 2026-09-01 evaluation date; missing snapshots remain missing.

The thirteen retrieval failures consist of source connectivity or TLS errors,
share-class/product-code mismatches, responses without usable stock-weight
columns and disclosed stock weights below the existing 85% threshold. These
categories require separate fixes; rerunning the same monolithic batch is not
a completeness strategy.

## Planner matrix

The zero-holding 1/4/7/10-month TWD 100 request reaches the modeled target with
47 eligible ETFs, seven additions and TWD 23,556.61 additional capital. The
seven additions exceed the owner-approved V5 maximum of five.

The zero-holding all-month TWD 3,000 request also reports `TARGET_MET`, but
uses thirteen additions and TWD 4,156,803.91. After constituent acquisition,
both positive-target zero-holding cases return three strategy variants. They
still do not meet the V5-4 portfolio-size direction.

The 0050 and 00929 holding cases now raise `AttributeError: 'int' object has no
attribute 'quantize'`. `calculate_weighted_overlap()` sums an empty shared-
constituent list as Python integer zero, then invokes the Decimal-only
`quantize()` method. This is a calculation defect exposed by real constituent
data, not a missing-data state.

The 0050 plus 00878 case still has zero eligible additions because 00878 has no
automated snapshot and `HOLDING_OVERLAP_UNAVAILABLE` excludes 198 candidates.
Unsupported-product and missing-price cases remain explicitly `UNAVAILABLE`.
The audit records per-case exceptions as `ERROR` so one calculation defect no
longer prevents the remaining matrix from being inspected.

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

V5-3A resolves this audited defect by applying the explicit evaluation date to
monthly-income and component projections. The 00929 acceptance replay now ends
paid history at 2026-08-14 while retaining the scheduled 2026-09-14 event in
the dividend evidence APIs. The audit findings above remain the pre-fix
snapshot rather than being rewritten as if the defect had not existed.

## Data blockers versus V5-4 algorithm blockers

V5-3 data work should proceed in this order:

1. acquire and reconcile official constituent snapshots so zero-to-N existing
   holdings do not remove the entire otherwise supported universe, starting
   with Cathay because 00878 is an acceptance holding and twenty-two targets
   share that source;
2. separate paid history from future scheduled payment evidence throughout the
   calculation-data projection, using 00929 as the acceptance case;
3. make full-market price and yield refreshes checkpointed and resumable, then
   resolve the measured redirect failures without suppressing rejected rows;
4. reduce stale, missing after-tax cash and incomplete component exclusions
   while preserving ACTUAL versus estimated semantics; and
5. add fund size, expense ratio, distribution period or stock dividend only
   after a verified official source and field contract exist.

V5-4 remains responsible for the independent algorithm findings:

- represent zero shared constituent weight as Decimal zero so valid disjoint
  portfolios do not crash allocation;
- solve with no more than five added ETFs;
- solve zero-to-N holdings rather than rejecting the entire market;
- compare complete whole-share combinations before calculating planning grade;
- return two or three materially distinct non-dominated plans when they exist;
- avoid treating additional capital as a benefit; and
- replace the current bounded best-effort, one-plan result only after
  deterministic replay and owner acceptance.

The post-V5-3A full-market refresh and retry evidence is recorded in
[`V5_3D_FULL_MARKET_REFRESH.md`](V5_3D_FULL_MARKET_REFRESH.md). It supersedes
the coverage counts in this pre-fix snapshot but does not rewrite the original
audit findings.

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

python -m backend.app.data_sources.constituent_batch_pipeline `
  --database <candidate.db> `
  --output <new-constituent-report.json> `
  --allow-network
```

The full JSON evidence records every exclusion code, exact request, result
snapshot, whole-share addition, capital amount, selected-month cash flow,
shortfall, strategy issue and 00929 paid/future event split.
