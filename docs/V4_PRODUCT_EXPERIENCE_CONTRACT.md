# V4 Product Experience and Dual Assessment Contract

## Purpose

V4 changes `GoodCat 股利喵` from a data-heavy analysis interface into a
beginner-facing ETF planning experience that remains feasible in Streamlit.
It preserves the V3 calculation, data-provenance and safety boundaries while
reorganizing the visible journey around one question:

> For the owner's selected dividend months and cash target, what should be
> added, how many whole shares are needed, how much capital is required, and
> what important trade-offs remain?

V4 starts locally after the owner accepted the V3-8 cleanup as sufficient.
Real-domain deployment and SEC-4 `READY` remain mandatory before public launch,
but they do not block local V4 implementation and page review.

## Product experience principles

1. Lead with the planning action and the result, not database or operational
   detail.
2. Explain one decision at a time in short Traditional Chinese sentences.
3. Keep advanced evidence available without making it the first screen.
4. Never hide missing data, failed risk gates, remaining target shortfalls or
   bounded-solver limitations behind a friendly visual treatment.
5. Preserve the public planner as stateless; targets and holdings are not saved.
6. Do not add order placement, real-time signals or performance guarantees.

## GoodCat character and visual direction

GoodCat is an original gray-and-white cat character. The personality is
usually relaxed and slightly lazy, but becomes attentive and helpful when the
owner starts planning.

The initial character states are:

- `IDLE`: lying down or resting on the home and empty states;
- `ATTENTIVE`: looking up while the owner enters months, targets or holdings;
- `WORKING`: actively checking information while an analysis is running;
- `READY`: presenting the completed allocation;
- `CAUTION`: calmly pointing out missing data, risk or remaining shortfall.

The supplied cat image is a mood and pose reference only. Production assets
must be original or have documented usage rights. Character imagery must not
replace text labels, result status or accessible state descriptions.

The initial light-theme palette is:

| Token | Value | Intended use |
| --- | --- | --- |
| Canvas | `#F7F7F4` | Main background |
| Surface | `#FFFFFF` | Cards and input groups |
| Primary text | `#343740` | Headings and body text |
| Secondary text | `#6F737C` | Supporting explanations |
| Cat gray | `#5B5E69` | Brand and primary action |
| Soft pink | `#DFA5B4` | Small character and selection accents |
| Border | `#D9DADF` | Card and widget separation |

Final tokens must pass readable text and primary-button contrast checks. Color
alone must not communicate success, risk or availability.

## Two distinct user-facing outcomes

V4 separates ETF historical quality from suitability for the owner's current
goal. Neither result may substitute for the other.

### 1. ETF historical quality grade

The frontend may show a deterministic grade:

```text
A+ / A / B / C / D / E / F
```

The underlying numeric score and rank remain internal. The grade describes the
available historical evidence for an ETF; it is not a buy/sell command and
does not mean the ETF is suitable for every owner.

The grade must:

- remain unavailable unless the core total-return and downside evidence exists;
- show `暫不評等` rather than `F` when required evidence is missing;
- use fixed, versioned thresholds rather than a market-relative percentile
  that changes merely because another ETF is added;
- disclose the methodology version, evidence period and data date;
- include short plain-language strengths, risks and missing-evidence notes;
- never allow yield, dividend amount, tax composition or payment timing to
  rescue failed data-quality, total-return or principal-risk gates.

`F` therefore means a complete evaluation produced the lowest grade. It never
means that the system lacked enough data.

### 2. Owner-goal allocation fit

The allocation result answers whether a complete whole-share portfolio fits
the submitted months, cash target, existing holdings and funding requirement.
It uses the existing `推薦配置`, `平衡配置` and `集中配置` result semantics and
continues to show fewer alternatives when a materially different, evidence-
supported plan does not exist.

The first result card must show:

- ETFs and whole shares to add;
- additional capital required;
- selected-month cash coverage and every remaining shortfall;
- the main reason the plan fits the goal;
- the most important risk or data limitation;
- solver status without falsely describing bounded best effort as optimal.

A high ETF grade does not guarantee high owner-goal fit. A high owner-goal fit
also does not override a failed ETF eligibility gate.

## Assessment synthesis

The external yield/performance/tax/fill/concentration formula is treated as a
research input, not as a replacement production algorithm. V4 retains the
strongest properties of both approaches:

- keep total return as the largest quality influence;
- keep downside performance as a separate factor rather than hiding it inside
  total return;
- keep cash yield subordinate to total return and principal protection;
- add fill success rate and fill duration only after their event definitions,
  observation window and missing-data behavior are tested;
- evaluate tax composition from official ACTUAL evidence when available and
  keep tax impact contextual to explicit user assumptions;
- evaluate constituent concentration at both individual-ETF and resulting-
  portfolio level instead of applying one blunt fixed penalty;
- preserve hard eligibility gates before any weighted grade or allocation
  optimization;
- preserve V3 whole-share, capital, overlap and selected-month optimization.

V4-1 must compare the current methodology with candidate revisions through
historical replay, missing-data cases and weight-sensitivity tests. A revised
weight set is adopted only when it improves defined outcomes without weakening
the existing risk gates. The initial external weights are not accepted as
defaults merely because they sum to 100%.

The calibration report must separately measure:

- negative-total-return rejection;
- downside-risk separation;
- stability of grades across observation dates;
- fill metric coverage and survivorship bias;
- effect of missing ACTUAL composition;
- individual-ETF and resulting-portfolio concentration;
- selected-month target coverage, capital and remaining shortfall;
- deterministic reproducibility.

## Streamlit implementation boundary

V4 remains a Streamlit frontend over the existing FastAPI backend.

- Prefer native theme configuration, containers, forms, segmented controls,
  pills, charts and status elements.
- Use the sidebar for navigation and owner-only global controls, not primary
  result content.
- Use session state only for the current browser interaction and GoodCat visual
  state; it must not persist public planner inputs.
- Render the page structure before slow analysis and reserve a stable result
  container with an accessible working state.
- Use custom HTML or CSS only for behavior or styling that native Streamlit
  cannot express safely; isolate and regression-test any required selectors.
- Keep calculation and eligibility logic in the backend, never in visual
  components or character-state code.

No programming-language migration or real-domain deployment is required to
implement or review this experience locally.

## V4 acceptance boundary

A V4 page is accepted only when it passes all of the following:

- its primary beginner task is apparent without operational knowledge;
- the GoodCat interaction supports rather than obscures the task;
- keyboard labels, text alternatives, contrast and narrow-screen layout remain
  usable;
- missing, zero, estimated and official values remain distinct;
- the two assessment outcomes cannot be mistaken for each other;
- public/private navigation and stateless planner boundaries remain intact;
- focused frontend, API contract, calculation and security regressions pass.

