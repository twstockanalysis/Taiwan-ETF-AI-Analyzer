# V4-6 Functional Integration Acceptance

Status: `IN_PROGRESS`

This document records functional evidence before the separate owner-led V4-7
page-by-page UI and UX review. Passing an item here does not accept a page's
visible field selection, wording or layout, and it does not select a release
candidate.

## Acceptance matrix

| Area | Required evidence | Status |
| --- | --- | --- |
| Public planning boundary | Anonymous zero-to-N holdings request remains stateless and schema-validated | Smoke verified |
| Whole-share allocation | Result plans preserve integer shares, capital, cash coverage, reasons and risks | Smoke verified |
| Dual assessment | Historical quality and owner-goal fit remain separate; no raw score, rank or confidence reaches public UI | Smoke verified |
| ETF exploration | Search, ranking, detail and comparison use the same `A+` to `F` or `暫不評等` contract | Smoke verified |
| Public/private API boundary | Owner-only routes remain protected and public routes do not require or persist owner identity | Smoke verified |
| Portfolio tax and reinvestment | Portfolio-level 1-to-20-year scenarios preserve tax and missing-data semantics | Pending |
| Data quality | Official, estimated, missing and zero values remain distinct across ingestion and APIs | Pending |
| Local security | Secret scan, dependency/runtime checks and complete security regressions pass | Pending |
| Running integration | FastAPI and Streamlit complete the primary journey using the local production-like configuration | Pending |
| Complete regression | Full backend and frontend automated suite passes on the final V4-6 commit | Pending |

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
- This smoke result closes only Slice 1. The document remains `IN_PROGRESS`
  until every pending matrix row is verified.

## Remaining sequence

1. Verify portfolio tax, reinvestment and long-term calculation contracts.
2. Verify official-versus-estimated data-quality and missing-value semantics.
3. Run local security and production-compose integration checks.
4. Run the complete automated regression and close V4-6 only if all evidence
   is green.
5. Start V4-7 with the frontend and backend running for owner-led page review.
