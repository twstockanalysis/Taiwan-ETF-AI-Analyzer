# Decision Profile Contract

## Scope

M11-1 introduces the first persisted decision inputs after the M10 calculation
contracts stabilized. It is deliberately limited to one public-site profile and
manual Taiwan ETF holdings. It does not provide accounts, access isolation,
broker synchronization, recommendations, decision records or trading.
M11-4 later adds assessment snapshots under the separate decision-record
contract; it does not change the M11-1 profile into a recommendation engine.

Because this is one mutable singleton with no account isolation, its write API
and Streamlit page are suitable only for a controlled single-user environment.
They must not be exposed to anonymous public visitors before write-access
controls are added.

## Fixed conditions

The singleton profile can persist:

- Fixed monthly after-tax cash target in TWD
- Analysis horizon from 1 to 50 years
- Historical data window from 1 to 10 years
- Optional generic cash-deduction rate from 0% to 100%

A missing deduction rate means that the user has not supplied that assumption.
It is distinct from a formal `0%` deduction.

## Manual holdings

The M11-5 batch editor accepts zero to any number of Taiwan ETF holdings and
starts with zero rows for a new profile. Each row has exactly two editable
values: ETF code and positive whole units. ETF codes must be unique. One batch
request atomically replaces the saved set, so an empty batch is a valid
zero-holding state.

The backend resolves reference price, trade date and source from the latest
stored `etf_daily_close`. These fields are read-only and must not be labeled as
real-time quotes. When no trustworthy stored close exists, all three remain
null; dependent holding-value and portfolio-comparison outputs become partial
instead of treating the price as zero. The original single-item, user-price API
remains only for M11-1 compatibility and labels those values `manual_legacy`.
ETF identity and classifications continue to come from `etf_master`.

## Current-holding analysis

M11-2 adds one read-only analysis over all saved manual holdings. The monthly
cash target belongs to the whole portfolio and is applied exactly once; it is
never repeated for every ETF. Each holding's historical gross distribution
cash is scaled by its saved units. Period `PRICE_RETURN` is annualized and then
weighted by saved current holding value before the existing M10 target
calculator runs once for the aggregated portfolio.

When the generic cash-deduction rate is present, the analysis derives one
aggregate deduction amount. It does not invent an income-tax, supplementary-
premium or other-cost breakdown. A missing deduction rate remains missing and
makes dependent outputs partial. If any holding lacks required distribution or
performance data, the portfolio input remains unavailable instead of treating
that holding as zero. A missing official close similarly makes the aggregate
holding value and every dependent scenario unavailable. A non-TWD distribution currency is also incompatible
with the saved TWD reference value and is never added without conversion.

The response separates per-holding historical facts from the portfolio
scenario. `UNAVAILABLE` means conditions or holdings have not been saved;
`PARTIAL` retains all calculable outputs plus stable unavailable fields.

## Safety and future use

Every API response declares `profile_scope=SINGLE_USER` and
`broker_connected=false`. M11-2 passes these persisted inputs into existing
M10 calculations while preserving their calculation modes, assumptions,
warnings and missing-value semantics. Neither the saved profile nor the
current-holding scenario is an investment recommendation.

M11-3 candidate analysis follows the separate
`CANDIDATE_HOLDING_ANALYSIS_CONTRACT.md` and never mutates this profile.

M11-4 follows `DECISION_RECORD_EXPORT_CONTRACT.md`. Saving a record reruns the
candidate analysis and appends an immutable snapshot. It never changes the
singleton conditions or manual holdings.
