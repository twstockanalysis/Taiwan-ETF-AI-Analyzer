# V4-6 Functional Integration Acceptance

Status: `COMPLETE`

This document records functional evidence before the separate owner-led V4-7
page-by-page UI and UX review. Passing an item here does not accept a page's
visible field selection, wording or layout, and it does not select a release
candidate.

## Acceptance matrix

| Area | Required evidence | Status |
| --- | --- | --- |
| Public planning boundary | Anonymous zero-to-N holdings request remains stateless and schema-validated | Verified |
| Whole-share allocation | Result plans preserve integer shares, capital, cash coverage, reasons and risks | Verified |
| Dual assessment | Historical quality and owner-goal fit remain separate; no raw score, rank or confidence reaches public UI | Verified |
| ETF exploration | Search, ranking, detail and comparison use the same `A+` to `F` or `暫不評等` contract | Verified |
| Public/private API boundary | Owner-only routes remain protected and public routes do not require or persist owner identity | Verified |
| Portfolio tax and reinvestment | Portfolio-level 1-to-20-year scenarios preserve tax and missing-data semantics | Verified |
| Data quality | Official, estimated, missing and zero values remain distinct across ingestion and APIs | Verified |
| Local security | Secret scan, deployment contracts and complete security regressions pass | Verified |
| Running integration | Native FastAPI and Streamlit services pass health and public/private boundary smoke checks | Verified |
| Complete regression | Full backend and frontend automated suite passes on the final V4-6 commit | Verified |

## Slice 1 — Core public contracts

Scope:

- public planner API contract;
- allocation-result API contract;
- ETF historical-quality-grade API and frontend validation;
- public assessment presentation semantics;
- public and owner API access boundaries.

Commands:

```powershell
.venv\Scripts\python.exe -m unittest `
  tests.test_public_planner_api `
  tests.test_allocation_results_api `
  tests.test_etf_api `
  tests.test_frontend_quality_grades_client `
  tests.test_frontend_assessment `
  tests.test_security_api_boundaries
```

Result on 2026-08-27: `37 tests passed` in 8.541 seconds.

Non-blocking runtime notices:

- FastAPI TestClient reported the repository's existing Starlette/httpx
  deprecation warning; no contract test failed.
- This smoke result established Slice 1 and did not by itself close V4-6.

## Slice 2 — Calculation, data and security contracts

The focused group covered long-term scenarios, portfolio projections, tax and
reinvestment, ACTUAL dividend components, data profiles, secret scanning,
frontend transport security and production deployment/smoke contracts.

Result on 2026-08-27: `76 tests passed` in 6.925 seconds.

## Slice 3 — Running local integration

FastAPI and Streamlit were started as temporary hidden local processes against
the current development database and an ephemeral owner token. The rehearsal
passed all six checks:

- API health;
- anonymous private-route denial;
- wrong-token denial;
- owner-token access;
- frontend availability;
- Streamlit health.

Both temporary processes were stopped after the smoke test. This is local V4
functional evidence only; Docker edge routing, TLS, DNS and public-host SEC-4
remain part of V4-8.

## Slice 4 — Complete regression

Commands:

```powershell
.venv\Scripts\python.exe -m compileall -q backend frontend tests deployment
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

Result on 2026-08-27: compilation passed and `985 tests passed` in 102.572
seconds.

Non-blocking notices were limited to existing dependency deprecations,
Streamlit's expected no-runtime warnings in bare tests and automatic Arrow
type coercion for one mixed-type test dataframe. No functional test failed.

## Decision

V4-6 is complete locally. It confirms functional contracts and running local
service boundaries, but does not accept page wording, field selection, visual
hierarchy or responsive experience. Those decisions belong exclusively to the
owner-led V4-7 page-by-page review. No release candidate is selected here.
