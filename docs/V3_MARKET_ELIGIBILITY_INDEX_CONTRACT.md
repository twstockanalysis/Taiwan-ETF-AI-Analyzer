# V3 market eligibility and internal assessment index

## Purpose

V3-2 replaces user-picked candidates with one server-built index over the
complete ETF master. It decides which products may enter V3-3 whole-share
optimization and preserves every exclusion as a stable code and plain-language
reason.

The index is historical and deterministic. It does not select shares, place an
order, issue a trading signal or guarantee a future distribution or return.

## Public request boundary

`POST /api/v1/allocation-plans/eligibility-index` reuses the V3-1 stateless
request:

- a fixed after-tax TWD target for every selected month;
- one or more selected months;
- zero to 500 existing ETF holdings with positive whole shares;
- a one-to-ten-year dividend-history window; and
- a generic cash-deduction assumption.

The request cannot override eligibility thresholds. Thresholds are fixed by
`DETERMINISTIC_MARKET_ELIGIBILITY_V3_2`, returned in the response and changed
only through a reviewed methodology version. The request and result are not
written to the owner profile or decision records.

## Product universe

Every row in `etf_master` appears in the public index. The initial allocation
scope supports ordinary equity ETFs. Bond and fixed-income, leveraged,
inverse, futures, commodity and multi-asset products remain visible but are
excluded with a stable product-scope reason. They are not silently compared
under equity rules.

## Hard gates

A supported ETF is eligible for addition only when all applicable gates pass:

1. a source-dated official reference close exists, is not future-dated and is
   no more than ten days old;
2. four-period `PRICE_RETURN` facts and payment-date dividend facts satisfy the
   existing 75% completeness and freshness rules;
3. historical payment-month stability is at least 50%;
4. after-tax cash contribution is calculable and positive;
5. estimated after-tax total return is at least 0% and the worst available
   supported-period price return is at least -20%;
6. one complete ACTUAL or ESTIMATED dividend-component mix exists and is not
   future-dated or stale; an estimated fallback remains an explicit trade-off;
7. when existing holdings are present, source-qualified portfolio constituent
   overlap is available and no more than 50%; and
8. V3-3 must enforce the returned 20% maximum candidate allocation against the
   actual integer-share solution.

Missing and incompatible data fail the affected gate. With zero existing
holdings, overlap is formally `NOT_APPLICABLE` with a numerical zero internal
starting fact; missing overlap for a non-empty portfolio is never converted to
zero.

## Internal score boundary

Eligible candidates receive the existing deterministic ETF-quality score for
server-side ordering. Total return and downside facts remain mandatory core
inputs; cash, stability and fresh official ACTUAL 76W evidence are bounded
secondary inputs. A score cannot reverse an exclusion.

The internal object also carries twelve Decimal-safe after-tax cash-per-share
facts for V3-3. Neither the quality score, score components, internal rank nor
an assessment-confidence label is part of the public response model.

## Reproducibility and data coverage

The public candidates are ordered by ETF code and include source dates,
component basis, overlap state and reasons. A SHA-256 snapshot identity covers
the normalized request, fixed rules and complete public item facts. Equivalent
facts on the same analysis date therefore produce the same identity.

ACTUAL and estimated-component counts remain separate. An estimated fallback
does not become official data. The index makes the current ACTUAL coverage gap
measurable so source review can be expanded without overstating availability.
