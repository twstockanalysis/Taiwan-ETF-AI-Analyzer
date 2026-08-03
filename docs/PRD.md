# Product Requirements

## Product

TW ETF AI Analyzer is a public Taiwan ETF cash-flow decision website for
individual investors with limited investment information or professional
analysis experience.

The product helps a user start from one self-selected Taiwan-listed ETF and
answer a practical question:

> How much capital is needed to support a fixed after-tax cash-flow target,
> and can that target be pursued without hiding a loss in total return?

The website analyzes ETFs only. It does not analyze individual stocks and is
not designed as a professional trading terminal.

## Primary users

The primary user:

- Wants recurring cash distributions from Taiwan-listed ETFs
- Has a fixed monthly cash-flow target
- Needs tax effects explained in plain language
- Is concerned that distributions may mask a loss in market value
- Wants transparent assumptions instead of a black-box recommendation
- May choose to spend, partially reinvest or fully reinvest distributions

Professional traders, institutional investors and users who require execution,
real-time quotes or portfolio optimization are not the primary audience.

## Product objective

For one base ETF selected by the user, the website must:

1. Estimate gross and after-tax cash flow by payment month.
2. Calculate the capital required for a fixed cash-flow target.
3. Show the shortfall when the available capital cannot meet that target.
4. Evaluate distributions together with market-value change and costs.
5. Compare distribution-use and reinvestment scenarios.
6. Explain the tax-source composition, including official `54C`, `76W` and
   other disclosed components, without treating a tax code as a universal tax
   conclusion.
7. Optionally add a small number of complementary ETFs when monthly coverage
   is requested.
8. Reject or warn about combinations that improve payment-month coverage or
   apparent tax efficiency at the expense of total-return quality.

The website provides historical analysis and scenario estimates. It does not
guarantee future distributions, tax outcomes, market value or principal.

## Decision priority

Every analysis and recommendation must apply this order:

```text
total-return and principal-risk checks
-> after-tax cash-flow feasibility
-> tax-efficiency improvement
-> optional monthly-payment coverage
```

Tax efficiency and monthly payment coverage must never override a failed
total-return or data-quality check.

## Core user flow

```text
select one base ETF
-> enter available capital and fixed monthly cash-flow target
-> review the base ETF alone
-> compare after-tax cash flow and total return
-> compare reinvestment scenarios
-> optionally request monthly payment coverage
-> review complementary ETFs, exclusions and trade-offs
```

The monthly cash-flow target remains fixed when available capital changes.
Additional capital lowers the yield required to reach the same target; it does
not automatically increase the target.

## Required analysis outputs

### Cash flow

- Gross distribution cash
- Estimated tax and supplementary-premium effects
- After-tax usable cash
- Payment-month distribution from January through December
- Monthly and annual target coverage
- Required capital and funding shortfall
- Missing or insufficient source-data warnings

### Performance and principal

- Market-value gain or loss
- Gross distributions received
- Estimated taxes, supplementary premiums, transaction costs and other modeled
  costs
- After-tax total gain or loss
- After-tax total-return rate
- Warnings for high distributions accompanied by negative total return,
  persistent price or NAV decline, failure to recover after distributions, or
  material peer underperformance

The calculation must not present distributions alone as investment profit.
For a portfolio ledger, the common accounting identity is:

```text
after-tax total gain or loss
= ending holding value
+ net withdrawn cash
- initial capital
- later external contributions
- externally paid costs not already reflected above
```

For a no-reinvestment breakdown, the equivalent result is:

```text
after-tax total gain or loss
= market-value gain or loss
+ gross distributions
- taxes and modeled premiums
- transaction costs
```

Reinvested distributions are internal portfolio cash flows and must not be
counted again as external profit. Taxes, premiums and costs must be deducted
exactly once: either through the net cash and ending-value ledger or as an
explicit deduction, but never through both paths.

### Reinvestment scenarios

The first version must compare:

- No reinvestment
- Reinvest only cash above the fixed target
- Reinvest a user-defined percentage
- Reinvest all distributions

Each scenario must show usable cash, reinvested cash, ending units, ending
portfolio value, estimated tax cost and after-tax total return. Historical
replay and forward-looking estimates must be labeled separately.

### Tax explanation

The first tax-estimation scope is limited to Taiwan tax-resident individuals
holding Taiwan-listed ETFs. The result is an estimate and is not tax advice.

The website must:

- Preserve official source codes and distinguish ACTUAL components from
  estimates
- Keep `EST_REALIZED_CAPITAL_GAIN` separate from official `76W`
- Treat formal `76W = 0%` as available data and missing `76W` as missing data
- Model `54C`, `76W`, other disclosed components and applicable supplementary
  premiums through explicit, versioned assumptions
- Support user tax assumptions when individual circumstances change the result
- Explain that a higher `76W` ratio is not automatically better for every user
- Avoid labels such as "tax free" unless the modeled rule and user assumptions
  support that conclusion

### Optional monthly-payment combination

Monthly payment coverage is initially the default planning goal and must later
be available as an explicit user option.

When enabled, the website may add one to three complementary ETFs to the base
ETF. A candidate must pass:

- Data-completeness and freshness requirements
- Total-return and downside-risk checks
- Distribution stability checks
- After-tax cash-flow contribution checks
- Holding-overlap and concentration checks
- High-distribution but weak-total-return exclusions

The result must explain why each ETF was included, which month it supports,
which candidates were excluded and what trade-offs remain.

## Analysis modes and data semantics

The product must distinguish:

- Historical facts from scenario assumptions
- Market-price return from total return
- Gross cash flow from after-tax usable cash
- Withdrawn cash from reinvested cash
- Formal zero from missing data
- Official ACTUAL composition from estimated composition

Forecasts must expose their lookback window and assumptions. Missing data is
never silently converted to zero, and a result with insufficient data must be
unavailable or visibly qualified rather than assigned a neutral score.

## Existing delivered capabilities

- ETF master search, classification and detail
- 1M, 3M, 6M and 1Y market-price return
- Performance ranking and 2–4 ETF comparison
- Dividend history, payment dates and distribution summary
- ACTUAL dividend-component handling, including official `54C` and `76W`
- Source-document retention, freshness and data-quality coverage
- January-through-December monthly-income API
- FastAPI-backed Streamlit website with automated contract tests

These capabilities form the data layer. The next product work adds the decision
calculation layer.

## Core principles

1. Optimize for comprehensibility before professional-market detail.
2. Protect total-return quality before optimizing tax or payment months.
3. Keep the user's monthly cash-flow target fixed unless the user changes it.
4. Use official, traceable data whenever available.
5. Never convert missing values to zero.
6. Never mix performance periods, metric definitions, currencies or tax bases.
7. Never present estimated composition as official tax-source composition.
8. Make assumptions, exclusions, risks and data limitations visible.
9. Keep calculations deterministic and explainable before adding AI assistance.
10. Access public frontend data only through FastAPI and protect contracts with
    automated tests.

## Out of current core scope

- Individual-stock analysis
- Professional trading-terminal features
- Broker login or account synchronization
- Automatic order placement
- Real-time trading signals or market timing
- Guaranteed distribution, return, tax or principal outcomes
- Fully personalized tax filing or professional tax advice
- Unexplainable AI scoring or unconstrained portfolio optimization
- Mobile native applications
- Unverified scraping
- OCR-based automatic tax-code inference

External market or broker APIs can be evaluated only after the core website,
decision calculations and deployment architecture are complete.
