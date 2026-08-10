# Decision Record and Excel Export Contract

## Scope

M11-4 can save one candidate-holding analysis as an immutable SQLite snapshot.
The server reruns the candidate analysis from the submitted assumptions before
writing the record; it never accepts a frontend-supplied analysis result as the
source of truth.

A record preserves:

- Candidate ETF identity and the original proposed units, TWD reference price,
  optional holding-overlap estimate, monthly-coverage switch and eligibility
  rules
- The complete current-versus-proposed portfolio analysis response
- Stable assessment rationale and exclusion reason codes
- Deterministic alternatives for failed or missing gates
- Trade-offs, unavailable fields and permanent safety notes

This is an assessment history, not a recommendation log. It does not connect a
broker, update `manual_holding`, place an order or guarantee an outcome.

## Immutability

`decision_record` is append-only through the application. The API exposes
create, list, read and export operations only; it deliberately exposes no
update or delete operation. Later changes to fixed conditions, holdings or
market data do not modify an existing snapshot. A later comparison creates a
new record with a new ID and timestamp.

The initial release remains `SINGLE_USER`. Decision-profile and record writes
must be access-controlled before anonymous public deployment.

## Outcome

The stable outcome is one of:

```text
ELIGIBLE
INELIGIBLE
NOT_EVALUATED
UNAVAILABLE
```

`NOT_EVALUATED` is used when monthly candidate judgment was explicitly
disabled. It must not be interpreted as eligible. Missing overlap, deductions
or historical facts remain explicit and are never converted to zero.

## Excel workbook

The export is generated from the saved snapshot, never from current mutable
profile state. It contains:

```text
決策摘要
分析比較
理由與風險
持倉快照
限制與輸入
```

Numeric currency, percentage, unit and date cells remain typed Excel values.
Blank dependent results mean unavailable, not zero. The workbook includes the
record ID, immutable-snapshot warning, user-entered-price warning and no-broker
boundary. It contains no macros and performs no trading action.
