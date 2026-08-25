# Product Requirements

## Product

The official product name is `ETF奈米戶`. It is a Taiwan ETF cash-flow planning
website for beginners and individual investors with limited investment
information or professional analysis experience.

The product starts from the user's fixed after-tax cash-flow target, selected
payment months and zero to N existing Taiwan-listed ETF holdings. It answers:

> Which ETFs and how many whole shares need to be added, how much additional
> capital is required, and what risks or data limits remain?

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

For a user-defined target and current portfolio, the website must:

1. Accept a fixed after-tax cash target, selected payment months and zero to N
   existing ETF holdings.
2. Build the eligible candidate universe from the supported Taiwan ETF market;
   the user must not need to choose candidate ETFs or allocations first.
3. Return which ETFs to add, the non-negative whole-share quantity for each and
   the required additional capital.
4. Estimate gross and after-tax cash flow by payment month and show every
   remaining target shortfall.
5. Evaluate distributions together with market-value change and costs.
6. Compare distribution-use and reinvestment scenarios at portfolio level.
7. Explain the tax-source composition, including official `54C`, `76W` and
   other disclosed components, without treating a tax code as a universal tax
   conclusion.
8. Reject or warn about combinations that improve payment-month coverage or
   apparent tax efficiency at the expense of total-return quality.
9. Explain inclusions, exclusions, alternatives, assumptions and risks without
   exposing an ETF-quality score or assessment-confidence label in the UI.

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
enter fixed after-tax cash target
-> choose the months in which that target should be received
-> enter zero to N existing ETF holdings
-> let the service evaluate the eligible Taiwan ETF universe
-> review ETFs to add, whole shares and required additional capital
-> review month-by-month target coverage, alternatives, exclusions and risks
-> optionally review portfolio-level tax and reinvestment scenarios
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

### Automatic portfolio allocation

The public V3 planner is stateless and does not save the submitted holdings.
It automatically evaluates the supported candidate universe instead of asking
the user to preselect candidate ETFs or enter allocations.

A candidate must pass:

- Data-completeness and freshness requirements
- Total-return and downside-risk checks
- Distribution stability checks
- After-tax cash-flow contribution checks
- Holding-overlap and concentration checks
- High-distribution but weak-total-return exclusions

The result must use whole shares and explain why each ETF was included, how
much capital it consumes, which selected months it supports, which candidates
were excluded and what trade-offs remain. Existing holdings remain visible
even when they fail an add-more eligibility gate; V3 does not silently sell or
replace them.

The optimizer follows a deterministic priority order:

```text
hard data and risk gates
-> maximize selected-month after-tax target coverage
-> minimize required additional capital
-> reduce unnecessary additions, concentration and overlap
-> stable ETF-code tie-break
```

Only a result with a proved optimum may be labeled optimal. A bounded or timed
best-effort result must say so and retain its remaining shortfall.

The beginner-facing result always starts with `推薦配置`. When formal
constituent evidence produces a materially different feasible allocation, the
website should also show `平衡配置` and/or `集中配置`. Two or more configurations
are preferred, but the system does not fabricate a fixed count. `平衡配置`
reduces unnecessary constituent overlap. `集中配置` favors stronger recent
total-return evidence and similar constituent exposure without weakening the
same data, downside or concentration gates. Explanations remain short and use
plain language.

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
- Fixed-target cash-flow and no-reinvestment total-return calculations
- Taiwan individual-tax and four reinvestment scenarios
- Explainable monthly-payment candidate inclusion and exclusion
- Single-user saved conditions and manual holdings without broker connectivity
- Current-portfolio analysis and read-only candidate addition comparison
- FastAPI-backed Streamlit website with automated contract tests

These capabilities form the data and deterministic decision-calculation
layers used by V3. The current owner-only profile remains available, but the V3
planning entry must be public, stateless and usable with zero existing
holdings. Real-domain deployment and final SEC-4 acceptance occur after V3 and
the page-by-page information-architecture review, before public launch.

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
11. Keep internal ETF-quality scores and confidence labels out of the frontend;
    show allocation fit, reasons, evidence limits and risks instead.
12. A public planning request must not persist holdings, targets or results.

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

Broker execution and account synchronization remain optional after the core V3
allocation flow. The website does not place orders, provide real-time trading
signals or guarantee future distributions, returns, tax outcomes or principal.
