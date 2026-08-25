# V3-8 Page acceptance matrix

V3-8 reviews one page at a time. A page is accepted only when its primary
beginner task is clear, nonessential fields are removed or relocated, missing
data remains distinct from zero, and public safety boundaries remain visible.

| Order | Page | Primary task | Initial audit | Status |
| ---: | --- | --- | --- | --- |
| 1 | Home | Start a cash-flow allocation or choose a simple ETF exploration path | Core planner was absent from the home entry cards; API URL, database type, import batches and technical coverage dominated the page | Revised, awaiting owner review |
| 2 | Dividend planner | Enter target, months, holding years and 0-N holdings; receive allocation, capital and tax estimates | Technical history and cash-deduction inputs obscured the beginner flow; tax assumptions dominated the primary row | Revised, awaiting owner review |
| 3 | ETF detail | Understand one ETF's identity, performance, distributions, composition and risks | Target analysis and single-ETF tax forms overlap with the public portfolio planner and may need relocation or reduction | Pending |
| 4 | ETF comparison | Compare 2-4 ETFs on decision-relevant facts | Monthly-gap solver overlaps with automatic allocation; input and result fields need review | Pending |
| 5 | ETF search | Find an ETF and continue to its detailed information | Asset-type filtering and comparison entry distracted from the direct search-to-detail path; pipe-separated rows did not keep fields aligned | Revised, awaiting owner review |
| 6 | Performance ranking | Explore comparable historical price-return periods | Ranking evidence is useful; filters, metrics and explanatory copy need consolidation review | Pending |
| 7 | Dividend data quality | Understand whether official distribution data is available | Public transparency is useful, but operational review-queue fields may belong to owner operations | Pending |
| 8 | Owner profile | Maintain optional saved conditions and records | Deferred account/broker work must stay out; overlap with the public stateless planner needs review | Pending |
| 9 | Website administration | Inspect data coverage, freshness and import failures | Operational data was exposed on the public homepage | Relocated, awaiting owner review |
| 10 | Global navigation and responsive acceptance | Reach public tasks without exposing internal concepts | Material icons adopted with the home review; final route order and public/private boundaries remain pending | In progress |

## Dividend planner input decision

- Steps 1 through 5 use the same prominent heading level.
- Holdings remain optional and only require ETF code plus integer units; the
  latest stored official close is supplied by the system.
- Holding deletion requires selecting a row first; the delete action only
  appears after selection. Add and delete actions sit below the input table.
- The holdings table keeps a compact fixed-width selection column, hides column
  menus, and automatically orders completed rows by ETF code with blanks last.
- Month pills remain individually selectable, with every-month, odd-month and
  even-month shortcuts.
- Dividend reinvestment is a separate choice between cash use and full
  reinvestment.
- Enter-key form submission is disabled; only visible actions submit or change
  the form.

## Home acceptance decision

Keep:

- `ETF nano cat` brand name and the approved slogan;
- one prominent link to the public cash-flow planner;
- secondary links to search, ranking, comparison and data completeness.

Remove from the home page:

- FastAPI URL and health implementation details;
- database engine name;
- individual performance-period coverage grid;
- raw ACTUAL/76W event numerators;
- data-pipeline names, import batch IDs, record counts and error messages;
- manual refresh control for internal overview data.

The complete data-count, coverage, freshness and recent-import overview now
appears on the owner-unlocked `Website administration` page. The public home
page no longer requests the system-overview endpoint.

The underlying API fields are not deleted. During the dividend-quality and
owner-page reviews, public transparency fields and owner-only operational fields
will be assigned to their final destinations.

## ETF search acceptance decision

- Use `搜尋&詳細資料` for both the page title and navigation label.
- Keep keyword, management type and page-size controls; the asset-type selector
  is removed because this search experience currently covers non-bond ETFs.
- Remove the comparison-page shortcut so the primary path is search to detail.
- Present results in stable columns for name/code, management type, listing
  date, fund size and expense ratio. Selecting the name/code opens detail while
  preserving the search state.
- Do not imitate quote, price-change or volume fields from the visual reference
  until the list API provides verified values for those fields.
