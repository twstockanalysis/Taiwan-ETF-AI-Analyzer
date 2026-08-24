# V3 automatic allocation engine contract

## Purpose

V3 turns the existing ETF data and deterministic calculation layers into the
core `ETF奈米戶` planning result:

> Given a fixed after-tax cash target, selected payment months and zero to N
> existing ETF holdings, which ETFs should be added, how many whole shares are
> needed and how much additional capital is required?

The result is a transparent historical-data scenario. It is not an order, a
real-time trading signal, a promise of future distributions or a guarantee of
principal or total return.

## Public and stateless boundary

The V3 planner is a public FastAPI-backed flow. A request and its result are
not written to the decision profile, decision records, logs or shared
Streamlit cache. Operational logs may retain bounded technical metadata but
must not contain submitted holdings or cash targets.

The existing owner-only saved profile remains a separate optional workflow.
Public planning does not require an owner token, user account or broker link.

## Required request

Each request contains:

- `target_after_tax_cash_twd`: the fixed amount required in each selected month;
- `target_months`: a non-empty, unique subset of January through December;
- `existing_holdings`: zero to 500 unique Taiwan ETF codes with positive whole
  shares for every supplied row; and
- explicit versioned tax and cost assumptions required by the calculation.

Zero holdings is valid. A formal zero target is valid and returns no required
addition. Missing assumptions remain missing and may make dependent results
unavailable; they are never converted to zero.

The target applies independently to every selected month. For example, a
3,000 TWD target for January, March and May means at least 3,000 TWD of modeled
after-tax cash in each of those months, not a 9,000 TWD annual average that may
be concentrated in one month.

Existing holdings are fixed starting facts. The first V3 engine may recommend
only non-negative additional shares and must not silently sell, replace or
fractionalize an existing holding.

## Server-built candidate universe

The server constructs the candidate universe from supported Taiwan-listed
ETFs. The user does not preselect candidates or enter allocations.

Before optimization, every add-more candidate must pass versioned gates for:

1. ETF identity and supported product type;
2. reference-price availability and freshness;
3. payment-date history and selected-month distribution stability;
4. after-tax cash-flow calculability;
5. total-return and downside-risk requirements;
6. dividend-composition provenance and missing-data rules;
7. constituent freshness, overlap and concentration when required; and
8. bounded request and calculation resource limits.

Bond, leveraged, inverse, futures or multi-asset products are not silently
treated like ordinary equity ETFs. A product type is either explicitly
supported by its own rules or excluded with a reason.

An existing holding that fails an add-more gate remains in the current
portfolio calculation. It is marked `NOT_ELIGIBLE_FOR_ADDITION` with reasons;
the engine does not pretend it is absent and does not add more shares to it.

## Integer allocation model

For each eligible ETF `i`:

```text
h_i = existing whole shares
x_i = recommended additional whole shares, integer and x_i >= 0
p_i = source-dated reference price per share
c_i = modeled transaction cost for x_i shares

required additional capital
= sum(x_i * p_i + c_i)
```

For each selected month `m`:

```text
modeled after-tax cash_m
= sum((h_i + x_i) * after_tax_cash_per_share_i,m)

shortfall_m
= max(target_after_tax_cash_twd - modeled_after_tax_cash_m, 0)
```

Cash-per-share inputs use actual historical payment dates and explicitly
labeled historical normalization or scenario assumptions. Events outside a
selected month remain visible but do not satisfy another month's target.

The solver must use Decimal-safe inputs and return whole shares. It must not
solve with fractional shares and round upward afterward because that can
change capital, concentration, tax and coverage results.

## Deterministic objective order

The objective is lexicographic, not one opaque weighted score:

1. obey every hard eligibility, data and principal-risk gate;
2. minimize total selected-month after-tax shortfall;
3. when all selected months are covered, minimize required additional capital;
4. minimize unnecessary ETF additions;
5. minimize concentration and validated constituent overlap within their
   configured bounds; and
6. break otherwise equal results by stable ETF-code order.

Internal deterministic scores may order eligible candidates or bound search,
but they cannot override a failed gate. ETF-quality scores and assessment-
confidence labels are never returned in the public frontend payload.

The engine reports one of:

- `TARGET_MET`: every selected month meets the target;
- `PARTIAL`: a bounded best result exists but one or more months remain short;
- `NO_ELIGIBLE_ALLOCATION`: no addition passed the required gates; or
- `UNAVAILABLE`: required data or assumptions prevent a valid calculation.

Optimality is reported separately as `PROVED_OPTIMAL`, `BOUNDED_BEST_EFFORT`
or `NOT_APPLICABLE`. Only `PROVED_OPTIMAL` may be described as the lowest-
capital or optimal result.

## Required response

The public result includes:

- contract and methodology version;
- calculation timestamp and source as-of dates;
- normalized target months, assumptions and current holdings;
- each ETF to add, whole shares, reference price, estimated cost and supported
  months;
- total required additional capital;
- month-by-month current cash, added cash, total cash, target and shortfall;
- resulting holdings and concentration;
- inclusion reasons and risk explanations;
- excluded candidates and stable reason codes;
- at least one alternative when a materially different feasible result exists;
- missing, stale or estimated-data warnings; and
- the non-advice and non-guarantee statement.

The UI presents the final allocation fit, reasons and risks. It does not show
ETF-quality scores, score components, confidence labels or buy/sell signals.

## Reproducibility and safety

Equivalent requests against the same immutable input snapshot and methodology
version must return the same result. The response identifies that snapshot so
the result can be reproduced after market data changes.

The engine must fail closed when a required value is missing, stale,
incompatible or outside its supported model. Formal zero remains distinct from
missing data. Existing tax, total-return and no-double-counting ledger rules
remain authoritative.

No V3 endpoint places an order, connects to a broker, claims real-time pricing
or predicts a guaranteed future distribution.

## Delivery boundaries

- V3-1 exposes the public zero-to-N holdings and target-month request flow.
- V3-2 builds the full-market eligibility and internal assessment index.
- V3-3 implements the deterministic whole-share allocation solver.
- V3-4 presents the primary result, alternatives and exclusion reasons.
- V3-5 adds 3-year, 5-year and 10-year total-return evidence and long-term
  scenarios.
- V3-6 extends tax and 1-to-20-year reinvestment calculations to the complete
  resulting portfolio.

Accounts, imports and read-only broker APIs are optional extensions and do not
block the public stateless allocation flow.
