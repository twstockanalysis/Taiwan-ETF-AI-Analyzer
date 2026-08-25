# V3-8 Page acceptance matrix

V3-8 reviews one page at a time. A page is accepted only when its primary
beginner task is clear, nonessential fields are removed or relocated, missing
data remains distinct from zero, and public safety boundaries remain visible.

| Order | Page | Primary task | Initial audit | Status |
| ---: | --- | --- | --- | --- |
| 1 | Home | Start a cash-flow allocation or choose a simple ETF exploration path | Core planner was absent from the home entry cards; API URL, database type, import batches and technical coverage dominated the page | Implemented, awaiting owner review |
| 2 | Cash-flow planner | Enter target, months and 0-N holdings; understand allocation, capital, risks and long-term outcomes | Core function exists, but the single long form and result depth need progressive-disclosure review | Pending |
| 3 | ETF detail | Understand one ETF's identity, performance, distributions, composition and risks | Target analysis and single-ETF tax forms overlap with the public portfolio planner and may need relocation or reduction | Pending |
| 4 | ETF comparison | Compare 2-4 ETFs on decision-relevant facts | Monthly-gap solver overlaps with automatic allocation; input and result fields need review | Pending |
| 5 | ETF search | Find an ETF and continue to detail or comparison | Filters and row fields need beginner relevance review | Pending |
| 6 | Performance ranking | Explore comparable historical price-return periods | Ranking evidence is useful; filters, metrics and explanatory copy need consolidation review | Pending |
| 7 | Dividend data quality | Understand whether official distribution data is available | Public transparency is useful, but operational review-queue fields may belong to owner operations | Pending |
| 8 | Owner profile | Maintain optional saved conditions and records | Deferred account/broker work must stay out; overlap with the public stateless planner needs review | Pending |
| 9 | Global navigation and responsive acceptance | Reach public tasks without exposing internal concepts | Material icons adopted with the home review; final route order and public/private boundaries remain pending | In progress |

## Home acceptance decision

Keep:

- brand name and one-sentence value statement;
- one prominent link to the public cash-flow planner;
- secondary links to search, ranking, comparison and data completeness;
- simple counts for ETFs with performance and distribution data;
- latest public performance and distribution dates;
- a concise no-order, no-signal and no-guarantee statement.

Remove from the home page:

- FastAPI URL and health implementation details;
- database engine name;
- individual performance-period coverage grid;
- raw ACTUAL/76W event numerators;
- data-pipeline names, import batch IDs, record counts and error messages;
- manual refresh control for internal overview data.

The underlying API fields are not deleted. During the dividend-quality and
owner-page reviews, public transparency fields and owner-only operational fields
will be assigned to their final destinations.
