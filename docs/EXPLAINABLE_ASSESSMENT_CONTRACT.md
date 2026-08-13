# Explainable Assessment Contract

The second-version assessment starts with a deterministic evidence-gate
baseline. It is returned with the existing read-only candidate-holding
analysis and does not require an external model, API key or paid service.

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

The methodology identifier is
`DETERMINISTIC_EVIDENCE_GATES_V1`. This identifier allows saved decision
records and later model-generated explanations to disclose which deterministic
contract produced the underlying assessment.
