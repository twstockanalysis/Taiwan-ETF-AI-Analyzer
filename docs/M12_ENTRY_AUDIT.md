# M12 Entry Audit Gate

Status: **required before M12; not yet executed**.

## Canonical direction to reconfirm

The audit must start from the product redefinition recorded after M9 in commit
`03a9635` (`docs: redefine ETF cash-flow decision roadmap`) and reconcile it
with the current `docs/PRD.md` and `docs/ROADMAP.md`.

That confirmed direction defines the website as a public Taiwan ETF cash-flow
decision tool for individual investors with limited professional information.
It analyzes ETFs only and applies this order:

```text
total-return and principal-risk checks
-> after-tax cash-flow feasibility
-> tax-efficiency improvement
-> optional monthly-payment coverage
```

## Required audit work

Before any M12 implementation branch is created:

1. Inventory every public Streamlit page, navigation entry and user action.
2. Inventory every FastAPI analysis and write endpoint used by the website.
3. Map each post-M9 PRD objective and required output to one of:
   `DELIVERED`, `PARTIAL`, `MISSING`, `DEFERRED` or `OUT_OF_SCOPE`.
4. Verify the core flow from base ETF through cash flow, total return,
   reinvestment, optional monthly coverage, current holdings and candidates.
5. Recheck formal-zero, missing-data, currency, tax-basis and source-traceability
   semantics against implementation and tests.
6. Recheck that individual stocks, professional trading-terminal features,
   broker login, order placement, real-time signals and opaque AI optimization
   remain outside the current website.
7. Identify incomplete M11 product work separately from true M12 automation,
   operations and deployment work.
8. Confirm how singleton decision-profile writes will be protected before an
   anonymous public deployment.
9. Produce a written gap report with blocking and non-blocking items.
10. Obtain and record the user's confirmation of the reconciled website
    direction and function list.

## Entry acceptance

M12 may begin only when the audit report exists, no unresolved blocking product
gap is mislabeled as deployment work, and the user has explicitly confirmed
the reconciled direction and scope. Completing M11 alone does not satisfy this
gate automatically.
