# V3 allocation results contract

## Purpose

V3-4 turns the V3-3 whole-share calculation into a beginner-facing result.
The public endpoint is `POST /api/v1/allocation-plans/allocation-results`.
Requests and results remain stateless and are not written to a profile.

## Result strategies

Every valid response contains `推薦配置`. It is the default best-fit result
under the published deterministic priority order, but it is described as
optimal or lowest-capital only when the nested V3-3 result reports
`PROVED_OPTIMAL`.

When formal constituent data supports a materially different feasible result,
the response may also contain:

- `平衡配置`: gives preference to lower constituent overlap so the result is
  not unnecessarily concentrated in the same underlying stocks; and
- `集中配置`: gives preference to eligible ETFs with stronger recent modeled
  total return and more similar constituent exposure. It may have higher
  volatility and does not receive a weaker data, downside or 20% allocation
  gate.

Two or more strategies are preferred when they are genuinely different. The
server returns one to three plans and explains why an alternative is missing.
It never changes an ETF code or share count merely to fill a fixed number of
tabs. Without source-backed industry attribution, the focused result does not
claim that its exposure is an AI, semiconductor or other named theme.

All strategy searches retain the complete eligible candidate set. Formal
pairwise constituent comparisons are bounded to the first ten internally
ranked eligible candidates for predictable runtime; candidates without the
required comparison remain available to the solver but do not receive a
balance or focus preference.

## Simple public explanation

The public page shows, in this order:

1. strategy name and one-sentence explanation;
2. required additional capital, number of added ETFs and target status;
3. ETF code and name, whole shares to add, source-dated reference price,
   required capital and supported months;
4. current cash, added cash, modeled cash, target and shortfall by selected
   month;
5. optional resulting holdings, risks and excluded candidates; and
6. transaction-cost, bounded-optimality, non-advice and non-guarantee notes.

The page does not show internal quality scores, ranks, score components or
confidence labels. Exclusion reasons describe failed data or risk gates and
are not buy or sell commands.

## Product and data boundaries

Active equity ETFs, including codes ending in `A`, are not excluded merely by
their code suffix. They must pass the same product, history, price,
distribution, composition, return, downside and constituent gates as other
equity ETFs. Missing history remains a data limitation rather than an
unsupported-product label.

The result uses saved official closes and historical payments. It is not a
real-time quote, order, future distribution guarantee or principal guarantee.
