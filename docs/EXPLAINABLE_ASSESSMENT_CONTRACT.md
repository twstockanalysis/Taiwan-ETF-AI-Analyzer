# Explainable Assessment Contract

The second-version assessment combines deterministic evidence gates with two
transparent 0–100 scores. It is returned with the existing read-only
candidate-holding analysis and does not require an external model, API key or
paid service.

## Purpose and boundary

The assessment organizes evidence that the website already calculates. It
does not predict future performance, assign a buy/sell signal, rank candidates
with an opaque score or override any eligibility gate. A future language-model
summary may explain this structured result, but must not change its factors or
outcome.

The fixed factor order is:

1. Data quality
2. Total return and principal risk
3. After-tax cash flow
4. Optional payment-month coverage

Payment timing therefore cannot rescue a candidate that fails completeness,
freshness, historical distribution stability, total return, downside risk,
overlap, concentration or after-tax cash-flow requirements.

## Scores

The ETF quality score uses these original weights when data is available:

- After-tax total return: 45%
- Downside return: 20%
- After-tax cash rate: 15%
- Distribution stability: 10%
- Official ACTUAL 76W average ratio: 10%

Available weights are normalized when a non-core metric such as official 76W
is missing. The score remains unavailable unless both total return and downside
return exist. This prevents high dividends or a high 76W ratio from producing
a high quality score without performance evidence.

The portfolio-fit score is based primarily on ETF quality (70%), followed by
after-tax cash-flow contribution (15%) and the portfolio total-return change
(15%). It remains unavailable when the ETF quality score is unavailable.

The current database does not contain automatically maintained ETF constituent
holdings. User-entered overlap remains a risk assumption and is not included in
either score. Automatic constituent ingestion and portfolio-weighted overlap
must be implemented before diversification becomes a scored metric. Low
overlap must never compensate for weak performance, and high overlap must be
evaluated together with portfolio performance rather than receiving an
automatic fixed penalty.

The UI displays the two scores, their components and missing metrics. It does
not display a separate assessment-confidence label; missing evidence remains
visible through omitted components, unscored metrics and gate explanations.

## Outcomes

- `INSUFFICIENT_DATA`: at least one core factor cannot be evaluated.
- `BLOCKED_BY_GATE`: at least one core factor fails its configured threshold.
- `NEEDS_REVIEW`: core gates do not block the scenario, but optional coverage
  or secondary information still needs human judgment.
- `GATE_ALIGNED`: the scenario passes the configured core gates and the
  requested payment-month contribution.

`GATE_ALIGNED` means aligned with the current user-supplied scenario and rules;
it is not an investment recommendation or guarantee.

## Explainability

Each factor exposes a status, plain-language rule, observed evidence and the
existing machine-readable reason codes. No aggregate score is calculated,
because a weighted score could hide a failed principal-risk or data-quality
gate.

The methodology identifier is `DETERMINISTIC_MULTI_SCORE_V2`. This identifier
allows saved decision
records and later model-generated explanations to disclose which deterministic
contract produced the underlying assessment.
