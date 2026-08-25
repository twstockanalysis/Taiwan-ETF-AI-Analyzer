# V3-5 Long-term Scenario Contract

## Purpose

V3-5 adds portfolio-level historical evidence and long-term scenarios after
V3-4 has produced one or more whole-share allocation plans. It does not replace
the allocation result and does not add a second ETF-selection method.

The public endpoint is:

```http
POST /api/v1/allocation-plans/long-term-scenarios
```

It is public and stateless. The request, holdings and result are not persisted,
no broker is connected, and no order is created.

## Strategy alignment

The response embeds the unchanged V3-4 allocation result and returns exactly
one `plan_evidence` item for each plan, in the same strategy order. Therefore a
frontend that selects `RECOMMENDED`, `BALANCED` or `FOCUSED` must display only
the matching historical and scenario evidence.

## Historical evidence

Historical evidence is a portfolio reconstruction, not a stored performance
record. For every resulting holding it uses:

- the plan's fixed resulting whole-share quantity;
- daily closes from the same source as the plan's reference price;
- only dates shared by every holding in the plan;
- actual payment dates and TWD distribution amounts;
- the request's generic cash-deduction percentage; and
- no distribution reinvestment.

The calculation is:

```text
ending total = ending market value + after-deduction cash distributions
total return = ending total / starting market value - 1
annualized return = total-return factor^(365.2425 / observation days) - 1
```

The response always includes four independent rows:

```text
AVAILABLE_HISTORY
3Y
5Y
10Y
```

`AVAILABLE_HISTORY` uses the longest compatible common history. Each fixed
window starts on the first common close no more than 14 days after its target
start and ends on the last common close no more than 14 days before its target
end. A missing common price range, non-positive start value, mixed currency or
distribution with an in-period event date but no payment date makes the
affected row `UNAVAILABLE`. Missing values never become zero.

### Raw-price limitation

Stored official closes are currently raw closes. The project does not yet have
a verified ETF split and reverse-split adjustment series. Historical evidence
therefore returns `price_basis=RAW_OFFICIAL_CLOSE` and the public page warns
that a unit change can distort the estimate. The response must not be described
as an official adjusted total-return index.

The fixed-share reconstruction is hypothetical: it asks how the final ETF mix
would have behaved over the compatible history. It does not claim that the user
actually owned those shares throughout that period.

## Ten-year scenarios

Scenario inputs are complete trailing one-year portfolio observations ending
at the latest common close and moving backward in twelve-month steps. At least
two available observations are required. Otherwise all scenarios remain absent
with an explicit issue.

When enough evidence exists, V3-5 uses:

| Scenario | Historical percentile |
| --- | ---: |
| Conservative | 25 |
| Base | 50 |
| Optimistic | 75 |

Each annual assumption is compounded from year 0 through year 10 as a
total-value index starting at 100. The index is not invested capital, a cash
balance or a forecast. Distributions are represented inside the annual
total-return assumption and are not added a second time.

V3-6 may reuse the historical evidence but will replace this simple index with
portfolio tax and one-to-twenty-year cash/reinvestment ledgers.

## Public safety boundary

The response and page must not include:

- ETF-quality scores, components or internal ranks;
- assessment-confidence labels;
- buy, sell or timing instructions;
- guaranteed distributions, returns or principal outcomes; or
- claims that a scenario is a forecast.

The beginner-facing page shows the matching allocation first, then the four
historical rows, the raw-price limitation, the three annual assumptions and a
native ten-year index chart.
