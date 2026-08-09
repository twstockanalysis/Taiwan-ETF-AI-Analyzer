# Monthly-Payment Combination Contract

## Scope

M10-5 creates a stateless planning scenario from one base ETF and one to three
candidates already chosen by the user. It does not search the full market,
persist a portfolio, rank active versus passive management, or promise future
monthly distributions.

## Historical facts and assumptions

Historical facts come from actual dividend `payment_date` records and the
latest `PRICE_RETURN` records for `1M`, `3M`, `6M` and `1Y`. Payment months are
stable only when their observed-year ratio meets the configured distribution-
stability threshold.

The user explicitly supplies:

- Candidate unit prices used for annual cash-rate estimates
- Candidate scenario allocations
- A generic cash-deduction rate
- Optional base-to-candidate holding-overlap estimates
- Lookback years, maximum additions and eligibility thresholds

The generic deduction rate is a scenario input, not an individualized tax
conclusion. Missing holding overlap is never converted to zero.

## Eligibility gates

Each candidate is checked before payment-month contribution is considered:

1. Data completeness and freshness
2. Historical distribution stability
3. Positive estimated after-tax cash contribution
4. Minimum estimated after-tax total return
5. Minimum downside return across available supported periods
6. Maximum holding overlap when supplied or required
7. Maximum candidate allocation

Estimated annual after-tax cash rate is:

```text
(historical cash per unit / lookback years / unit price)
× (100% - cash deduction rate)
```

Estimated after-tax total return is the latest one-year price return plus that
annual after-tax cash rate. This is a simple screen, not a forecast or a
distribution-reinvestment calculation.

## Selection and explanations

Candidates that pass every required gate are ordered deterministically by:

1. Number of currently missing base-payment months supported
2. Higher estimated after-tax total return
3. Higher estimated after-tax cash rate
4. ETF code

Selection then proceeds until the configured one-to-three ETF limit is reached
or no candidate supports an uncovered month. Every selected and rejected ETF
returns reason codes, plain-language messages and affected months. The base ETF
is always returned as the visible anchor.

## Missing and zero semantics

- Missing base payment data makes the combination unavailable.
- Missing performance, cash or downside data fails the affected eligibility
  gate rather than becoming zero.
- Missing holding overlap is a visible trade-off by default and an exclusion
  when overlap is configured as required.
- Formal `0%` overlap and formal numeric zero values remain available values.
- Active/passive and bond/non-bond classifications are descriptive facts only.

All results carry the label `月配組合情境，非投資建議或保證`.
