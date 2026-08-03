# Cash-flow and total-return calculation contract

## Purpose

M10-2 establishes a deterministic calculation boundary before user profiles,
recommendation scores, persistence or frontend analysis flows are introduced.

The contract separates three things that must not be treated as equivalent:

- cash distributions received by the investor
- change in the market value of the holding
- total gain or loss after taxes, premiums and costs

The first implementation is stateless. It does not populate the
`etf_performance.TOTAL_RETURN` metric and does not add a database table.

## Analysis modes

Every calculation declares exactly one mode:

| Mode | Meaning |
| --- | --- |
| `HISTORICAL_REPLAY` | Uses observed prices, distributions and costs within a completed period. |
| `SCENARIO_ESTIMATE` | Applies explicit assumptions to a defined future or hypothetical period. |

Historical facts and scenario assumptions cannot be combined without the
caller first labeling the result as a scenario estimate.

## Currency and units

- One calculation uses exactly one ISO 4217 currency.
- The first version performs no foreign-exchange conversion.
- All money, rates and quantities use `Decimal`; binary floating point is not
  accepted inside the calculation service.
- Percentage values use percentage points: `5` means 5%, not `0.05`.
- Intermediate values remain unrounded.
- Public money results are rounded to 2 decimal places with `ROUND_HALF_UP`.
- Public percentage results are rounded to 6 decimal places with
  `ROUND_HALF_UP`.
- A missing value remains `None`; it is never converted to formal zero.

## Date basis

- The analysis period is inclusive of `period_start` and `period_end`.
- Distribution cash is assigned by actual `PAYMENT_DATE`.
- Beginning and ending holding values use actual `TRADE_DATE` observations.
- A caller cannot silently substitute announcement, ex-dividend or record date
  for payment date.
- A caller cannot combine values from different date windows without receiving
  a machine-readable unavailable reason.

## Fixed after-tax cash-flow target

The monthly target is a user condition. It remains fixed when available capital
changes.

```text
annual after-tax target
= monthly after-tax target * 12

after-tax usable cash
= gross distribution cash
- distribution tax
- supplementary premium
- other distribution costs

reference after-tax cash rate
= after-tax usable cash / reference capital

target coverage
= projected after-tax usable cash / annual after-tax target

required capital
= annual after-tax target / reference after-tax cash rate

funding shortfall
= max(required capital - available capital, 0)
```

The required-capital result is unavailable when reference capital, gross cash
or any modeled deduction is missing. It is also unavailable when the resulting
after-tax cash rate is zero or negative. A zero monthly target is a valid formal
zero and produces no funding shortfall; it must not be treated as missing.
For that formal-zero target, coverage is reported as `100%` and required
capital and funding shortfall are both `0`, even when no reference rate is
needed. Missing distribution inputs still leave after-tax usable cash
unavailable.

## Total-return ledger

The canonical ledger identity is:

```text
after-tax total gain or loss
= ending holding value
+ net withdrawn cash
- initial capital
- later external contributions
- externally paid costs not already reflected above

after-tax total-return rate
= after-tax total gain or loss / initial capital
```

`net withdrawn cash` contains cash that left the investment and was not
reinvested. Reinvested distributions remain inside ending holding value and are
not added again. Costs already reflected in ending value or net withdrawn cash
are not entered again as externally paid costs.

For a no-reinvestment breakdown, the equivalent identity is:

```text
market-value gain or loss
= ending holding value - initial capital

after-tax total gain or loss
= market-value gain or loss
+ gross distributions
- distribution tax
- supplementary premium
- transaction costs
- other externally paid costs
```

The calculator tests must reconcile these two identities for equivalent input.

## Pure calculator behavior

The first calculator service is deterministic and has no database, network or
clock dependency. It accepts only validated contract models and returns a
result model without mutating its input.

- `calculate_cash_flow_target` calculates the fixed after-tax cash target.
- `calculate_total_return` applies the canonical portfolio ledger identity.
- `calculate_no_reinvestment_total_return` applies the equivalent distribution
  breakdown and must reconcile with the canonical ledger for equivalent input.
- A negative after-tax usable cash amount remains visible, while coverage,
  required capital and funding shortfall remain unavailable.
- Zero or negative reference cash rates never enter a division operation.
- Missing values produce field-specific issues; formal zero values remain
  calculable wherever the denominator rules allow them.

## Scenario estimate

The scenario calculator is intentionally separate from historical replay. Its
input context must use `SCENARIO_ESTIMATE`, and every result retains the
`NO_REINVESTMENT` policy. It is an arithmetic projection, not a forecast or a
claim that distributions will continue.

```text
ending holding value
= initial capital * (1 + annual price return rate) ^ projection years

cumulative gross cash
= initial capital * annual gross cash rate * projection years

cumulative cash deductions
= cumulative gross cash * cash deduction rate

cumulative after-tax cash
= cumulative gross cash - cumulative cash deductions

after-tax total gain or loss
= ending holding value + cumulative after-tax cash - initial capital
```

The annual gross cash rate is applied to initial capital each year. Cash is not
reinvested, so it does not compound. Price return compounds only the holding
value. The first version accepts projection periods from 1 through 50 years,
cash deduction rates from 0% through 100%, and price return assumptions no
lower than -100%.

All five numeric assumptions must be explicit. If any one is missing, scenario
outputs remain unavailable with `MISSING_INPUT`; missing assumptions are never
silently replaced by zero. A formal zero assumption remains calculable. Zero
initial capital produces formal zero money results, but its percentage return
is unavailable with `NON_POSITIVE_INITIAL_CAPITAL`.

## Unavailable results

An unavailable numeric result is `None` and includes one or more stable reason
codes. Initial reason codes are:

| Reason | Meaning |
| --- | --- |
| `MISSING_INPUT` | A required source value or assumption is unavailable. |
| `MIXED_CURRENCY` | Inputs use more than one currency. |
| `DATE_BASIS_MISMATCH` | Inputs do not use the required period or date basis. |
| `NON_POSITIVE_INITIAL_CAPITAL` | A return rate has no positive denominator. |
| `NON_POSITIVE_AFTER_TAX_CASH_RATE` | Required capital cannot be inferred from the reference cash rate. |
| `NEGATIVE_AFTER_TAX_USABLE_CASH` | Modeled deductions exceed gross distribution cash. |

Formal zero remains a calculable value when the relevant formula allows zero.
Missing values, invalid denominators and mismatched data never receive a zero
result or a neutral score.

## M10-2 boundaries

M10-2 may add pure models, services, tests and documentation. It does not add:

- database schema or migrations
- user accounts or persisted profiles
- recommendation scores
- automatic trading
- tax advice
- claims that historical distributions will continue

FastAPI and Streamlit integration begin only after the pure calculation
contract passes table-driven tests.
