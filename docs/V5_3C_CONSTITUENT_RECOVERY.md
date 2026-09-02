# V5-3C official constituent recovery

## Decision

The measured automated-source failures were reduced from thirteen ETFs to five
without weakening the shared completeness gate. The full calculation-quality
universe improved from 116/157 ETFs and 18/21 issuers to 129/157 ETFs and 19/21
issuers. Issuer coverage now passes its 90% threshold, but ETF coverage remains
`NO_GO` at 82.165605%, below 90%.

This is a bounded data-source improvement, not a complete database or launch
decision. Cathay, BlackRock and five source-specific products remain
unavailable. V4-8, deployment and SEC-4 remain paused.

## Reproducible evidence

- Base code: `origin/main@d4cc17c`
- Evaluation date: `2026-09-02`
- Input candidate SHA-256:
  `7def54f0b00338193858746014d3fecb99a18e7bc0d36e1ebebf55844eaefaaa`
- Result candidate SHA-256:
  `91a0e0911e44f3785ae15f66ecea7de2a27994abdd4d7b555093d56d8af9addb`
- Result candidate size: `14,282,752` bytes
- SQLite integrity: `ok`
- Foreign-key violations: `0`
- Local candidate, checkpoint and audit artifacts:
  git-ignored `reports/v5-3c-20260902/`
- Consolidated audit size: `2,458,229` bytes

The source candidate was copied before import and was not overwritten.

## Thirteen-failure reconciliation

Eight ETFs now import from their existing official adapters:

- `00714`, `00918`, `00946` and `00982A` recovered when the transient DNS,
  TLS or connectivity failure did not recur.
- `00645`, `00652` and `00700` now accept their complete Fubon official asset
  pages at 87.8471%, 88.4294% and 89.8784% disclosed stock weight. The Fubon-
  specific parser requires an accompanying official non-stock asset table when
  stock weight is below 90%; the shared 90% parser default is unchanged.
- `00728` now ignores one formally zero stock row and reconciles the remaining
  thirty positive positions exactly to First's official 97.19% stock-asset
  total. Zero is not converted to missing, and a negative or malformed row
  remains rejected.

Five ETFs remain unavailable with observed source-backed reasons:

- `0061`: Yuanta PCF identifies the ETF but exposes zero direct stock rows and
  instead one ETF plus one futures position. Nested ETF and futures exposure is
  not relabeled as direct equity overlap.
- `00625K`: Fubon's official PCF request links to an unrelated `00717` asset
  page. No currency-share-class alias is assumed.
- `00643K`: Capital's official ETF catalog does not expose this currency share
  class, so no internal fund ID can be verified.
- `00924`: Fuh Hwa's official asset workbook discloses only 54.789% direct
  stocks plus 2.980% futures and no reconciled complete stock-asset total.
- `009812`: Nomura identifies the product but discloses a 96.6% underlying ETF
  position and a 2.74% futures position, not direct stock constituents.

Cathay's official page still returned an edge-service HTTP 500 during the
2026-09-02 verification. Its twenty-two calculation targets remain
`SOURCE_NOT_AUTOMATED`. BlackRock's one target remains access-protected. No
access protection, certificate validation or identity check was bypassed.

## Checkpoint and resume contract

The batch command accepts `--checkpoint <path>` and `--resume`. After every
attempt it atomically replaces a versioned checkpoint containing only ETF code,
issuer, outcome, source date, disclosed stock weight, constituent count and a
bounded error string. It does not store source payloads, cookies or secrets.

On resume, only prior `FAILED` items are fetched again. Prior `IMPORTED` and
`UNCHANGED` items are returned as `SKIPPED_COMPLETED`, so a rerun does not
repeat completed network work. The checkpoint must name the same database and
must have the supported schema version.

The live acceptance replay attempted thirteen codes on the first pass and
imported eight. The resume pass attempted only the five remaining failures and
skipped all eight completed codes.

## Planner impact

The post-import candidate was audited with the zero-shared-overlap correction
from Issue #93 / PR #94 so data and calculation failures could be separated:

- A 0050 holding plus quarterly TWD 100 target now has 28 eligible additions
  and returns three plans without an exception, but the primary plan still adds
  six ETFs.
- A 00929 holding plus all-month TWD 3,000 target has 39 eligible additions and
  returns three plans without an exception, but the primary plan adds twelve
  ETFs and requires TWD 7,489,187.86. Issue #91 still owns the future-scheduled
  dividend projection defect, so this is not a final 00929 product result.
- A 0050 plus 00878 holding request still has zero eligible additions because
  the Cathay 00878 snapshot is unavailable.
- Zero-holding quarterly and all-month targets still add seven and thirteen
  ETFs respectively, exceeding the owner-approved maximum of five.

All eight audit cases completed without an allocator exception and retained
their full 263-candidate evidence. The remaining portfolio-size, capital and
plan-selection problems belong to V5-4 rather than further threshold
relaxation in V5-3.

## Remaining data boundary

Reaching the 90% ETF gate requires at least 142 of 157 targets, thirteen more
than the current 129. The twenty-three non-automated Cathay/BlackRock targets
are numerically sufficient, but coverage must remain `NO_GO` until a
reproducible official response is available. The five product-specific
unavailable cases must not be filled by copying another share class or by
flattening nested ETFs into direct stock constituents without a separate
reviewed contract.
