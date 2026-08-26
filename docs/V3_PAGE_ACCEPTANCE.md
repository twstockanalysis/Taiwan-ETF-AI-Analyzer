# V3-8 Page acceptance matrix

> Historical status: on 2026-08-26 the owner accepted the completed cleanup as
> the V3 baseline and closed further V3 page acceptance. Remaining page changes
> move to the V4 product-experience contract and are not V3 release blockers.

V3-8 reviews one page at a time. A page is accepted only when its primary
beginner task is clear, nonessential fields are removed or relocated, missing
data remains distinct from zero, and public safety boundaries remain visible.

| Order | Page | Primary task | Initial audit | Status |
| ---: | --- | --- | --- | --- |
| 1 | Home | Start a cash-flow allocation or choose a simple ETF exploration path | Core planner was absent from the home entry cards; API URL, database type, import batches and technical coverage dominated the page | Revised, awaiting owner review |
| 2 | Dividend planner | Enter target, months, holding years and 0-N holdings; receive allocation, capital and tax estimates | Technical history and cash-deduction inputs obscured the beginner flow; tax assumptions dominated the primary row | Revised, awaiting owner review |
| 3 | ETF detail | Understand one ETF's identity, performance, distributions, composition and risks | Target analysis and single-ETF tax forms overlap with the public portfolio planner and may need relocation or reduction | Pending |
| 4 | ETF comparison | Compare 2-4 ETFs on decision-relevant facts | Source-specific return controls and technical metric copy added clutter; the code-input label repeated the placeholder's meaning | Revised, awaiting owner review |
| 5 | ETF search | Find an ETF and continue to its detailed information | Asset-type filtering and comparison entry distracted from the direct search-to-detail path; pipe-separated rows did not keep fields aligned | Revised, awaiting owner review |
| 6 | Performance ranking | View the top 20 non-bond ETFs for one selected performance period | Asset type, page-size, pagination and comparison controls obscured the ranking task; pipe-separated results were difficult to scan | Revised, awaiting owner review |
| 7 | Dividend data quality | Review official distribution coverage and operational queues | Review-queue fields are operational rather than beginner-facing content | Relocated to owner navigation, awaiting owner review |
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

- `GoodCat 股利喵` brand name and the approved slogan;
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

The detailed `Dividend data quality` page is no longer part of public
navigation. After owner access is unlocked, it appears under `管理者功能` with
the other administrative pages.

## ETF search acceptance decision

- Use `搜尋&詳細資料` for both the page title and navigation label.
- Keep keyword, management type and page-size controls; the asset-type selector
  is removed because this search experience currently covers non-bond ETFs.
- Remove the comparison-page shortcut so the primary path is search to detail.
- Present results in stable columns for name/code, management type, listing
  date, fund size and expense ratio. Code and name are separate columns with
  code first. Selecting any cell in a row opens detail while preserving the
  search state; the table toolbar is hidden.
- Do not imitate quote, price-change or volume fields from the visual reference
  until the list API provides verified values for those fields.

## Performance ranking acceptance decision

- Use `績效排行榜` for the page title and place it immediately below `股利試算`
  and above `搜尋&詳細資料` in public navigation.
- Keep only period and management-type filters; the ranking is fixed to non-bond
  ETFs and defaults to 6M.
- Request and display only the filtered top 20. Remove page-size controls,
  pagination and the comparison-page shortcut.
- Present rank, name/code, selected-period return, data date and management type
  in a stable table. Selecting the name/code opens ETF detail.

## ETF comparison acceptance decision

- Remove the technical PRICE_RETURN introduction and the source-specific return
  button from the comparison page.
- Keep the 2-4 code input functional but hide its redundant visible label; the
  placeholder continues to explain the accepted input.
- Every non-home page now uses the same `返回首頁` entry immediately above its
  title. Context-specific return state remains in URLs for backward-compatible
  shared links, but is no longer rendered as a separate page button.
- Public sidebar pages use Streamlit's ungrouped navigation so there is no
  collapsible brand section; owner-only pages remain grouped under `管理者功能`.
