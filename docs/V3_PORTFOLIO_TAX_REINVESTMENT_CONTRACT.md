# V3-6 Portfolio tax and reinvestment contract

## Scope

`POST /api/v1/allocation-plans/portfolio-projections` is a public, stateless
extension of the V3-5 allocation and long-term-scenario response. It projects
the complete resulting whole-share portfolio for 1 to 20 years under the
conservative, base and optimistic gross total-return assumptions and four
distribution-use policies:

- `NO_REINVESTMENT`: distributions remain usable cash
- `EXCESS_ONLY`: only after-tax cash above the selected-month annual target is
  reinvested
- `CUSTOM_PERCENTAGE`: the requested percentage of after-tax cash is
  reinvested
- `FULL_REINVESTMENT`: all after-tax cash is reinvested

The request and result are not stored. The endpoint does not connect to a
broker, place orders, expose an ETF quality score or return a confidence label.

## Historical facts and missing data

For every resulting holding, the service annualizes TWD distribution events in
the requested history window by `payment_date`. An in-window event without a
payment date, a non-TWD event or a positive distribution without a complete
component mix makes the affected plan unavailable. A formal zero distribution
remains calculable.

The newest complete ACTUAL component event is preferred. A complete ESTIMATED
event is used only when ACTUAL is unavailable and remains labeled
`ESTIMATED_FALLBACK`. `EST_REALIZED_CAPITAL_GAIN` is never relabeled as official
`76W`. An official zero is preserved only when an ACTUAL component row
explicitly records `76W = 0`.

## Tax estimate

Rule snapshot `TW-INDIVIDUAL-2026.2` was verified on 2026-08-25. The model lets
the user choose either combined dividend taxation with an 8.5% credit subject
to the entered remaining annual cap, or separate 28% dividend taxation. It does
not choose the more favorable method. Official `76W` and estimated realized
capital gain are excluded from the modeled personal dividend income tax and
supplementary-premium base.

The supplementary NHI estimate uses 2.11%, a TWD 20,000 per-payment threshold
and a TWD 10,000,000 per-payment cap. Historical event count is annualized per
ETF to estimate payments per year; uneven future payments are not predicted.
The public page shows only the estimated individual income-tax amount and
supplementary-premium amount, not legal text.

Primary references:

- Taiwan NHI supplementary-premium formula and limits:
  <https://www.nhi.gov.tw/ch/cp-3283-34642-2589-1.html>
- Ministry of Finance resident dividend-tax methods:
  <https://www.etax.nat.gov.tw/etwmain/alien-tax-service/alien-individual-income-tax/3ARnVgk>
- Ministry of Finance withholding and trust income-format manual (`54C`,
  `76W`): <https://download.tax.nat.gov.tw/imx/IMX-USER-114.pdf>
- Ministry of Finance public-fund transaction-income explanation:
  <https://www.etax.nat.gov.tw/etwmain/tax-info/understanding/tax-q-and-a/national/individual-income-tax/basic-tax-question/scope/eKN76QZ>

## Projection accounting

V3-5 forward bands are gross before portfolio tax. For each band, the weighted
annual distribution rate is subtracted from gross total return to derive a
single portfolio price-return assumption. This prevents a distribution from
appearing once as cash and again as price appreciation.

Each year applies price return, estimates portfolio income tax and
supplementary premium, and allocates reinvested cash across holdings in
proportion to their gross distributions. Fractional units are allowed only in
the long-term model; the initial allocation remains whole-share.

The after-tax result is:

```text
ending holding value + cumulative usable cash - initial holding value
```

Reinvested cash is an internal transfer and is not added again. The annual cash
target is the per-selected-month target multiplied by the number of selected
months, not by twelve.

All outputs are estimates, not tax advice, investment advice, trading signals
or performance guarantees.
