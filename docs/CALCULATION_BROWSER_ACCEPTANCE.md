# V2 calculation browser acceptance

## Purpose

V2-13 validates the calculation experience against the isolated V2-12
candidate before V2 closes and the independent `SEC-X` security gate begins.
Automated checks establish API and Streamlit behavior; final owner acceptance
confirms the visible browser interactions.

The candidate database is local and ignored by Git:

```text
database/tw_etf-v2-12-20260820.db
```

## Acceptance fixture

The 2026-08-20 local run used explicit test-only values:

| Input | Value |
|---|---:|
| Monthly after-tax cash target | 3,000 TWD |
| Analysis period | 10 years |
| Historical data period | 3 years |
| Generic cash deduction | 0% |
| Existing holding | 0050, 1,300 units |
| Existing holding | 00918, 500 units |
| Candidate addition | 0056, 1,000 units at 30 TWD |

The holdings endpoint resolved the saved official closes to 103.80 TWD for
0050 and 33.64 TWD for 00918. These are candidate snapshot values, not live
quotes.

## Automated results

The native local smoke check passed all six boundaries: API health, anonymous
private denial, wrong-token denial, owner access, frontend HTTP availability
and Streamlit health.

The calculation checks produced:

| Flow | Result |
|---|---|
| Current holdings | `PARTIAL`; value 151,760.00 TWD, annual after-tax cash 6,093.50 TWD and target coverage 16.926389% |
| Monthly combination | `PARTIAL`; base 0050 plus 00918 and 0056 covers months 1, 2, 4, 5, 7, 8, 10 and 11; months 3, 6, 9 and 12 remain gaps |
| 0056 candidate addition | `PARTIAL`; `GATE_ALIGNED`, annual after-tax cash changes from 6,093.50 to 10,399.50 TWD and unavailable overlap remains an explicit trade-off |
| 0050 tax and reinvestment | `AVAILABLE`; four policies, zero calculation issues, 10-year horizon and `ESTIMATED_FALLBACK` component basis |

`PARTIAL` is expected where a field remains unavailable. It does not convert a
missing dividend yield or rejected 00918 constituent snapshot to zero.

## Defects closed by V2-13

Live candidate analysis exposed a repeating decimal when a multi-year dividend
total was annualized. The unbounded value exceeded the money model's decimal
limit and caused the 0056 candidate endpoint to return HTTP 500. Annualized
per-holding cash is now rounded to the six-decimal calculation boundary before
portfolio aggregation, and the same request returns HTTP 200.

The candidate also demonstrates why a correct arithmetic projection can still
be misleading: the available 1Y price returns are mechanically compounded over
the selected 10-year horizon. The formulas remain unchanged, but current-
holding, candidate-comparison and tax/reinvestment results now warn that the
large values are mechanical scenario outputs, not performance forecasts. The
tax result also returns and displays its projection horizon.

## Known data gaps

- 0050, 0056 and 00918 currently use complete estimated component mixes when a
  complete issuer ACTUAL event is unavailable. The page labels the fallback and
  does not relabel estimated capital gains as official 76W.
- The current UOB 00918 PCF response exposes incompatible foreign-stock rows
  totaling 49.20%. Automatic overlap therefore remains unavailable rather than
  zero.
- Some stored dividend events do not provide a per-event yield. Cash amounts
  remain calculable, while yield-dependent fields stay explicitly unavailable.

These gaps do not block cash-flow testing. They remain visible inputs for later
data refreshes and must not be described as complete official coverage.

## Owner browser checklist

Start FastAPI and Streamlit with the same candidate database and local-only
owner token as documented in `CALCULATION_CANDIDATE.md`, then open
`http://127.0.0.1:8501`.

1. Confirm the public home page and public ETF navigation render without an
   owner token.
2. Unlock owner features and confirm the private page contains 0050 with 1,300
   units and 00918 with 500 units.
3. Select **Analyze current holdings** and confirm the value, annual cash and
   target coverage render, together with the 1Y-to-10Y mechanical projection
   warning.
4. Compare a 0056 addition of 1,000 units at 30 TWD. Confirm the result renders
   instead of an error, missing overlap is not displayed as zero and the
   projection warning remains visible.
5. Compare 0050, 0056 and 00918, run the monthly-gap analysis with 0050 as the
   base, and confirm covered and remaining months are visible.
6. Open 0050 details and run the four tax/reinvestment policies. Confirm the
   estimated-component warning, 10-year horizon, four result rows and
   mechanical-projection warning are visible.
7. Relock owner features and confirm the private navigation entry disappears.

Owner confirmation on 2026-08-20: the replacement local token successfully
unlocked the private feature. The calculation-result interactions in steps 3
through 6 and the final relock check remain pending explicit confirmation.

V2-13 remains open until the owner confirms these visible interactions. After
that confirmation, the next milestone is `SEC-1`, not a `V3-X` feature PR.
