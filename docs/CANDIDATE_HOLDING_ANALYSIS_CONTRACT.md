# Candidate Holding Analysis Contract

## Scope

M11-3 compares the saved current portfolio with one user-supplied candidate
addition. The candidate code, proposed whole units, TWD reference price and
optional holding-overlap estimate are scenario inputs only. The endpoint never
writes `manual_holding` and does not create a decision record.

## Reused calculations

Both the before and after portfolios use the same M11-2 holding-snapshot
aggregation and M10 target calculator. The fixed monthly after-tax target is
therefore applied exactly once to each portfolio snapshot. Adding capital does
not increase the saved target.

Candidate eligibility reuses the M10-5 completeness, freshness, distribution
stability, total-return, downside, after-tax cash, holding-overlap,
concentration and payment-month rules. Reasons retain the existing stable M10-5
codes and plain-language messages.

## Decision order

Every response declares this fixed order from the post-M9 product
reconfirmation:

```text
total-return and principal-risk checks
-> after-tax cash-flow feasibility
-> tax-efficiency improvement
-> optional monthly-payment coverage
```

Improved payment-month coverage cannot override a failed data, total-return or
risk gate. Missing overlap remains missing and is never interpreted as zero.

## Missing values and limitations

A missing saved cash-deduction rate does not become `0%`. Candidate after-tax
cash remains unavailable and the M10-5 eligibility result includes
`MISSING_AFTER_TAX_CASH`. Before/after deltas are returned only when both values
are calculable.

The result is a no-trade scenario, not a recommendation or guarantee. Decision
records, alternatives across multiple candidates and Excel export remain later
M11 work.
