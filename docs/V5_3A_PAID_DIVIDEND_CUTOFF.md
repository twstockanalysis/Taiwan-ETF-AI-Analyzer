# V5-3A Paid-Dividend Analysis Cutoff

## Decision boundary

Dividend events remain stored and visible once announced. Historical cash-flow,
eligibility, allocation and tax-component calculations may use an event only
when its `payment_date` is on or before the request's analysis date. Missing
payment dates remain missing and are not inferred from announcement,
ex-dividend or record dates.

Calling the monthly-income repository without an analysis date preserves its
previous stored-history behavior for compatibility. Every date-aware planning
caller now supplies the analysis date explicitly.

## 00929 acceptance case

For an analysis dated 2026-08-31, the deterministic fixture contains:

- paid TWD 0.38 events on 2026-07-13 and 2026-08-14;
- an announced TWD 0.38 event with payment scheduled for 2026-09-14.

The monthly-income projection ends on 2026-08-14 and analyzes two events. The
stored event count remains three, and the dividend evidence repository remains
unchanged, so the 2026-09-14 event is still available to detail APIs. The
eligibility index does not emit `FUTURE_DIVIDEND_DATA` merely because the
scheduled event exists.

`etf_master.is_active = 0` continues to mean passively managed. Product support
is determined by the separate product-scope rules, so this value does not mark
00929 as inactive or delisted.

## Verification

Focused regression coverage verifies:

- cutoff and no-cutoff monthly-income behavior;
- 00929 support and latest paid date in the eligibility index;
- future component exclusion with a prior paid component fallback;
- analysis-date propagation through target analysis;
- preservation of paid-versus-future full-database audit evidence.

The complete test suite, bytecode compilation and `git diff --check` remain the
required PR acceptance gates. This correction removes one V5-3 calculation
blocker; it does not declare the database complete or make V5-4/V4-8 ready.
