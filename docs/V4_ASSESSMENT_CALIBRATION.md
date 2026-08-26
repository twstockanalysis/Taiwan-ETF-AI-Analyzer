# V4-1 Assessment Calibration and Grade Contract

## Decision

V4-1 keeps `DETERMINISTIC_MULTI_SCORE_V2` as the internal ordering baseline and
adds a public-safe `DETERMINISTIC_QUALITY_GRADE_V4_1` contract. The public model
contains only a fixed `A+` through `F` grade, short strengths and risks, missing
evidence and methodology identifiers. It never contains the raw score, rank or
confidence label.

The grade is not published merely because an internal score exists. Every
candidate returns `暫不評等` until the complete market snapshot passes all
three publication gates:

1. at least 30 ETFs have trustworthy core score evidence;
2. those ETFs cover at least 20% of the supported product universe;
3. no more than 50% of available total-return component scores are saturated
   at the 100-point ceiling.

These are minimum anti-misleading gates, not proof that a weighting method
predicts future results. A future methodology change still requires a new
identifier and regression evidence.

## 2026-08-26 local calibration evidence

The read-only calibration command was run against `database/tw_etf.db` with a
three-year request and analysis date 2026-08-26:

```powershell
python -m backend.app.check_assessment_calibration `
  --database database/tw_etf.db `
  --analysis-date 2026-08-26 `
  --history-years 3
```

Observed summary:

| Evidence | Count or result |
| --- | ---: |
| Complete ETF universe | 256 |
| Supported product universe | 192 |
| Provisional trustworthy grades | 6 |
| Published grades | 0 |
| Provisional grade distribution | 5 A+, 1 A |
| Total-return evidence available | 8 |
| Downside evidence available | 154 |
| After-tax cash-rate evidence available | 8 |
| Distribution-stability evidence available | 110 |
| Fresh official ACTUAL 76W score evidence | 0 |
| Provisional score minimum / median / maximum | 88.46 / 98.995 / 100 |

The available after-tax total-return component was saturated at 100 for its
small sample. This makes the provisional grade distribution unsuitable for
consumer display. The V4-1 publication decision is therefore `NOT_READY`, and
all public grade objects remain `UNRATED` with the calibration blockers.

## External-formula synthesis decision

The external yield/performance/tax/fill/concentration formula is not adopted as
a production score. V4-1 retains its useful ideas through explicit decisions:

- total return remains the largest influence;
- downside risk remains separate instead of being hidden in total return;
- fill success and fill duration are deferred until a corporate-action-adjusted
  event contract and adequate coverage exist;
- ETF constituent concentration is retained as risk evidence;
- resulting-portfolio constituent concentration remains a portfolio-level
  result, not a fixed single-ETF penalty;
- official tax composition remains optional evidence and cannot compensate for
  failed return, downside or data gates.

This preserves the strongest properties of both approaches without presenting
an unvalidated weight set as AI accuracy.

## Public contract

The full-market eligibility response and every added ETF in an integer
allocation contain `historical_quality_grade`:

- `status=RATED` with `grade=A+..F` only after publication readiness passes;
- `status=UNRATED` with `grade=null` when evidence or calibration is insufficient;
- a fixed threshold version and score-methodology identifier;
- at most three short strengths and risks;
- explicit unavailable evidence;
- no raw numeric score, internal rank or confidence field.

The owner-goal allocation result remains separate. A future displayed grade
must not change target-month coverage, whole-share quantities, required capital
or eligibility-gate behavior.

