# Tax and reinvestment scenario contract

## Scope and labels

M10-4 is an estimator for Taiwan tax-resident individuals holding
Taiwan-listed ETFs. Every response is labeled `情境估算，非稅務建議`.
Historical facts are returned under `historical_facts`; forward-looking tax,
price, distribution and reinvestment assumptions are kept in the request and
calculation result.

Stored `1Y`, `3Y` and `5Y` price returns are period returns. The API converts
them to an annualized price-return assumption before projection and returns the
source `price_return_period_code`. A missing or unsupported period code blocks
that assumption instead of treating a period return as annual.

The rule version shipped by the first Streamlit flow is
`TW-INDIVIDUAL-2026.1`, with an effective date of 2021-01-01. The date reflects
the current 2.11% supplementary-premium rate. Users must enter their own
effective income-tax assumptions because household filing circumstances can
change the result.

Official rule references checked for this version:

- National Health Insurance Administration, supplementary-premium formula,
  2.11% rate, TWD 20,000 per-payment threshold and TWD 10,000,000 cap:
  https://www.nhi.gov.tw/ch/cp-4516-74b0f-2613-1.html
- Ministry of Finance, resident dividend choices: 8.5% credit with an annual
  TWD 80,000 household cap, or 28% separate taxation:
  https://www.etax.nat.gov.tw/etwmain/alien-tax-service/alien-individual-income-tax/3ARnVgk
- Ministry of Finance, publicly offered securities-investment-trust fund unit
  transaction income is outside individual basic income:
  https://www.etax.nat.gov.tw/etwmain/tax-info/understanding/tax-q-and-a/national/individual-income-tax/basic-tax-question/scope/eKN76QZ

These references do not replace professional advice. The calculator does not
infer a user's filing method, available household credit, exemption status or
other income.

## Historical component selection

Only `component_basis=ACTUAL` rows are eligible. The server selects the newest
event whose disclosed component ratios are all present and total 99% through
101%, allowing official rounding. It returns the source event ID, event date
and every official component code. A formal `76W = 0%` remains available;
missing ACTUAL `76W` or other missing component data never becomes zero.

`EST_REALIZED_CAPITAL_GAIN` is not queried by this path and is never relabeled
as official `76W`.

## Tax model

For each projection year and official component:

```text
component cash = gross distribution cash * ACTUAL component ratio
income tax = component cash * user income-tax rate
tax credit = component cash * user credit rate
```

The annual credit is capped by the explicit rule input. By default it cannot
reduce modeled ETF income tax below zero; the user must explicitly allow the
credit to offset other tax.

Supplementary premium is estimated only for components explicitly marked
applicable. The annual component amount is divided into the user-entered number
of equal payments. A payment at or above the threshold is charged on its full
amount, subject to the per-payment cap. Actual uneven payment amounts are not
yet replayed, so this remains a scenario assumption.

## Reinvestment ledger

The calculator compares:

- no reinvestment;
- reinvestment of after-tax cash above the annual cash target;
- a custom percentage of after-tax cash; and
- full reinvestment.

Each year calculates tax and premium first, separates usable from reinvested
cash, applies the price-return assumption, then buys fractional units with
reinvested cash at the modeled year-end price.

```text
after-tax total gain or loss
= ending holding value + cumulative usable cash - initial holding value
```

Reinvested cash stays inside ending holding value and is never added again as
external profit. Each scenario exposes a total-return gate. The UI shows a
failure warning and never recommends a tax-preferred scenario over a failed
total-return result.

## Missing and formal-zero behavior

Missing distribution rate, price return, complete ACTUAL composition or a tax
assumption for any positive component blocks affected scenario outputs with a
stable reason. Formal zero rates and formal zero component ratios remain
calculable. A non-positive initial holding value cannot produce a return rate.
