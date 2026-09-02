# V5-3D full-market refresh evidence

This document records the reproducible V5-3D candidate refresh completed on
2026-09-02. It is evidence for Issue #100, not a launch decision. The source
database was copied to a separate candidate and was never overwritten.

## Fixed evaluation boundary

- Evaluation date: `2026-09-02`
- Universe: 263 ETFs
- Detail matrix: 263 ETFs by 18 fields
- Planner replay: eight cases, each retaining all 263 candidate decisions
- Source database SHA-256:
  `6a817e10ff4daeb09c9612490b3ff624a523780d46e3dc629210e80084712a76`
- Final candidate SHA-256:
  `5db79b9931c7fec74bb787f7c25de3b070b31e200345a04901fae7f41d6c4940`
- Candidate integrity: `ok`; foreign-key violations: 0

The evaluation date remains fixed even when a replay crosses midnight. Future
scheduled distributions remain visible as evidence but do not enter paid
history.

## Detail-field coverage

| Field | Available | Unavailable | Primary unavailable reason |
| --- | ---: | ---: | --- |
| identity | 263 | 0 | - |
| classification | 263 | 0 | - |
| listing date | 263 | 0 | - |
| fund size | 0 | 263 | no verified official AUM source |
| expense ratio | 0 | 263 | no verified total-expense source |
| price history | 238 | 25 | no official daily close |
| dividend history | 121 | 142 | no official dividend event |
| distribution period | 0 | 263 | source does not disclose the field |
| dividend yield | 121 | 142 | no official or calculable reference close |
| stock dividend | 0 | 263 | no verified source and schema field |
| estimated components | 106 | 157 | no complete eFortune estimate |
| ACTUAL components | 1 | 262 | no reviewed ACTUAL component notice |
| formal ACTUAL 76W | 1 | 262 | no reviewed ACTUAL 76W disclosure |
| 1M price return | 230 | 33 | insufficient price history |
| 3M price return | 223 | 40 | insufficient price history |
| 6M price return | 210 | 53 | insufficient price history |
| 1Y price return | 191 | 72 | insufficient price history |
| historical quality grade | 0 | 263 | publication evidence gate not met |

Missing fields remain unavailable. Estimated realized capital gain is not
formal 76W, and neither missing values nor unavailable fields are zero-filled.

## Yield recovery

The first refresh pass evaluated 1,236 missing-yield events, calculated 513 and
failed 723. Of those failures, 448 ended in a TWSE redirect loop. A direct
recheck of the same official endpoint returned HTTP 200 after cooldown, proving
that the cohort was a transient request-control failure rather than missing
market data.

The bounded correction stops automatic redirect following, retries only
transient `307`, `429`, `502`, `503` and `504` responses with exponential
backoff, persists newly downloaded official closes immediately, and commits
calculated yields every 25 records. Rerunning the pipeline therefore resumes
from the database instead of repeating completed source requests.

The recovery runs added 717 calculated yields. Final event coverage is
1,518/1,524. The six remaining events are explicit failures: one future
ex-dividend event and five events for which the official source has no prior
trading close. The retry correction also increased ETFs with any saved daily
close from 234 to 238 and ETFs with any usable yield from 120 to 121.

## Official constituent coverage

The full 263-ETF batch classified every product. It attempted all 134 automated
targets and imported 129; five source conversions failed. The calculation-
quality gate remains `NO_GO`:

- eligible ETF coverage: 120/157 (76.43%, minimum 90%);
- issuer coverage: 18/21 (85.71%, minimum 90%);
- 22 Cathay ETFs and one BlackRock ETF have verified disclosure but no
  automated import path;
- nine Capital snapshots are dated 2026-09-03 and are correctly future-dated
  for the fixed 2026-09-02 evaluation;
- conversion failures remain for 0061, 00625K, 00643K, 00924 and 009812.

Cathay is the highest-impact next acquisition cohort because 00878 is an
existing holding in the two-holding acceptance case.

## Planner replay

All eight cases completed without an exception and each records all 263 market
candidates. The replay did not change the allocation objective or solver.

| Case | State | Eligible | Plans | Aggregate added ETFs | Additional capital |
| --- | --- | ---: | ---: | ---: | ---: |
| zero holdings, quarterly TWD 100 | target met | 68 | 3 | 7 | 24,299.84 |
| 0050 holding, quarterly TWD 100 | target met | 40 | 3 | 5 | 22,649.38 |
| 0050 and 00878 holdings, quarterly TWD 100 | no eligible allocation | 0 | 1 | 0 | 0 |
| zero holdings, every month TWD 3,000 | target met | 68 | 3 | 13 | 839,577.78 |
| unsupported holding | unavailable | 0 | 1 | 0 | 0 |
| formal zero target | target met | 68 | 1 | 0 | 0 |
| 00929 holding, every month TWD 3,000 | target met | 52 | 3 | 12 | 772,705.73 |
| holding with missing reference price | unavailable | 0 | 1 | 0 | 0 |

`Aggregate added ETFs` is the audit's total across returned strategies; it must
not be misread as the size of one result card. V5-4 owns per-plan maximum-five
enforcement, non-dominated alternatives, whole-share optimization and personal
planning grades.

The 00929 reference check remains one deterministic boundary test, not a proxy
for market coverage. At the fixed evaluation date it uses 37 paid events
through 2026-08-14 and retains the scheduled 2026-09-14 event separately.

## Decision and next data work

The candidate is suitable as refreshed audit evidence but the database is not
complete and is not ready for launch. V5-3 should continue with these bounded
data cohorts, in priority order:

1. automate and validate Cathay constituents, beginning with 00878;
2. repair the five named constituent conversion failures and add the BlackRock
   path;
3. expand reviewed ACTUAL component and formal 76W acquisition without
   relabeling eFortune estimates;
4. reduce incomplete eFortune components and missing after-tax cash evidence;
5. add fund size, expense ratio, distribution period and stock dividend only
   after each official source and field contract is approved.

V5-4 separately owns solver behavior found by the replay. V4-8, deployment and
SEC-4 remain paused and are not authorized by this evidence.

## Reproduction

```powershell
python -m deployment.detail_data_candidate `
  --source <source.db> `
  --database <candidate.db> `
  --artifacts <artifact-directory> `
  --evaluated-on 2026-09-02 `
  --allow-network

python -m backend.app.data_sources.constituent_batch_pipeline `
  --database <candidate.db> `
  --output <constituent-report.json> `
  --checkpoint <constituent-checkpoint.json> `
  --allow-network

python -m backend.app.data_sources.dividend_yield_pipeline `
  --database <candidate.db> `
  --request-interval-seconds 1

python -m deployment.v5_full_database_audit `
  --database <candidate.db> `
  --evaluated-on 2026-09-02 `
  --output <audit.json>
```
