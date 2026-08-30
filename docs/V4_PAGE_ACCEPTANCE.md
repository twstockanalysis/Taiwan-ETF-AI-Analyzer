# V4-7 Page-by-page UI and UX acceptance

Status: `ACCEPTED`

V4-7 reviews the running Streamlit website one page at a time with the owner.
Functional correctness was established by V4-6; this stage decides whether the
visible experience is understandable and useful to an ETF beginner.

All accepted page changes remain on one V4-7 branch and pull request. The PR is
created only after the first page changes are ready, and it is merged only after
every in-scope page is accepted.

## Review rules

For each page, verify:

- the primary task is apparent without financial or operational expertise;
- fields are removed, added, renamed, reordered or relocated as needed;
- GoodCat supports the task without obscuring information;
- the primary action and next step are visually clear;
- missing, zero, estimated and official values remain distinct;
- loading, empty, partial and error states remain understandable;
- narrow-screen use, keyboard labels and text alternatives remain usable;
- public and owner-only information stays in the correct navigation boundary.

## Review order

1. Home — `ACCEPTED`
2. Planner input — `ACCEPTED`
3. Allocation result — `ACCEPTED`
4. Performance ranking — `ACCEPTED`
5. Search and detail entry — `ACCEPTED`
6. ETF detail — `ACCEPTED`
7. ETF comparison — `ACCEPTED`
8. Owner profile — `ACCEPTED`
9. Dividend data quality — `ACCEPTED`
10. Website administration — `ACCEPTED`
11. Global navigation and narrow-screen behavior — `ACCEPTED`

Owner acceptance was recorded on 2026-08-30 after the running pages were
reviewed. The final planner-result adjustment adds a happy, raised-paw GoodCat
state that implies a deserved reward after calculation without displaying the
reward object. The complete 1,040-test regression and Python compilation pass;
automated evidence supports but does not replace the owner's page acceptance.

## Home review

Current decision: awaiting owner inspection of the running V4 page.

Applied during review:

- shortened the Chinese slogan from `ETF規劃不踩雷` to `規劃不踩雷`;
- shortened the English slogan from `Easy ETF planning` to `Easy planning`;
- removed the visible descriptive image caption beneath the idle GoodCat;
- shortened the state label from `GoodCat｜陪主人慢慢想` to `陪主人慢慢想`;
- corrected the primary GoodCat message to `主人先想想在哪幾個月領股利，剩下的交給咪。`.
- removed the repeated `主人不用先挑 ETF` heading from the primary action
  card;
- reframed the primary introduction around `領罐頭錢`, optional current ETF
  holdings and GoodCat calculating the recommended plan and required capital.
- shortened the primary action label from `開始讓股利喵規劃` to `開始!`.
- shortened the secondary exploration heading to `也可以` and its three
  actions to `查查基本資料`, `看看績效` and `比較比較`.
- removed the three preparation cards from the homepage so it stays focused on
  the GoodCat identity, the `開始!` action and the three secondary page links;
  their instructions now sit beside the related controls on the planner page.
- changed the planner monthly-target heading and input unit from `（TWD）` to
  `(NTD)` for the requested consumer-facing wording.
- removed the separate idle-GoodCat card and state label, placed the unframed
  cat image to the left of the home introduction with both paragraphs on its
  right and the `開始!` action below, and revised the second introduction
  paragraph to hand recommendation and funding calculation to GoodCat.
- replaced the flexible horizontal container with fixed `1:4` image-and-copy
  columns after browser review showed the copy wrapping below the cat.
- removed the duplicated login, data-source and reference-only notice from the
  home action card because the planner page already carries its own notice.
- kept the two home introduction lines but removed the blank paragraph spacing
  between them.
- moved the `開始!` action into the right-hand copy column so the cat remains
  the only content in the left column.
- enlarged only the homepage `開始!` action, including its height, label and
  icon, while leaving the three secondary links visually subordinate.
- kept the homepage `IDLE` cat sleepy while replacing only the planner
  `ATTENTIVE` artwork with rounder eyes, forward ears and a more eager feline
  expression; the new production PNG uses real alpha transparency and the
  previous attentive asset remains available for rollback.
- changed planner sections 1 through 4 into separate bordered cards. Sections
  1, 2 and 4 now use the shorter titles `選擇月份`, `目標` and `庫存可留白`
  with the accepted beginner copy beside the actual controls; the holding card
  keeps the existing price-source explanation.
- changed section 5, `股息再投入與否`, into the same bordered-card treatment
  as planner sections 1 through 4 without changing its choices or default.
- renamed the optional tax expander from `稅務假設（可調整）` to the final
  consumer-facing label `稅務試算選項`.
- renamed planner section 2 from `目標` to the GoodCat-themed
  `罐頭錢目標`.
- rewrote the tax-expander introduction in the GoodCat voice, explaining that
  the owner may adjust the inputs or keep the defaults before GoodCat estimates
  income tax and supplementary health-insurance premiums.
- split the month card into an instruction-and-presets area on the left and a
  fixed three-column month grid on the right; months now follow four rows from
  January through December instead of wrapping according to available width.
- shortened the holding-period card description to `使用AI預測長期表現`.
- moved the latest-closing-price explanation below the holding action buttons
  so the primary input and `持股` action appear before secondary detail.
- shortened that closing-price explanation to state only that the price is
  taken from the close, or the previous close while the market is open.
- renamed the planner submit action to the shorter GoodCat voice
  `讓咪開始工作`.
- removed the repeated planner subtitle about choosing months, setting a target
  and not selecting candidate ETFs; the GoodCat card now follows the page title
  directly.
- replaced the short pre-submit disclaimer with the approved complete
  investment-risk wording and moved it to a small caption at the very bottom of
  successful configuration results; it is hidden before a result exists.
- moved the changing GoodCat status card from the page header to immediately
  above `讓咪開始工作`, keeping waiting, working, result and caution feedback
  beside the action that triggers calculation.
- changed the planner attentive-state label to `正在等主人` and its prompt to
  `如果都選完了，就「讓咪開始工作」吧！`, placing the next action directly
  beside the submit button.
- simplified the performance-ranking summary to show only the selected period
  and `前20名`; removed both the `排行榜 ETF` total metric and the repeated
  matching-result count below the ranking.
- increased `前20名` to the same responsive value size as the selected period
  and removed the extra vertical gap before the existing divider.
- aligned editable holding cells with the white input-field surface, locked the
  holding and performance table headers against menu and sort interactions,
  and hid the performance table toolbar; holding rows continue to normalize
  and sort automatically by ETF code after edits.
- pinned `排名` before the ETF code and name in the performance table so the
  visible data columns follow the expected ranking order.
- replaced the ranking dataframe selection UI with aligned, borderless table
  rows: the checkbox gutter is gone and every point across a result row opens
  that ETF's detail page while preserving the ranking filters for return.
- normalized pre-encoded ETF names before safe HTML output so names such as
  `期元大S&P黃金反1` no longer expose `&amp;` as visible text.
- left-aligned the holding-unit editor column so its empty `None` placeholder
  follows the same reading edge as the ETF code input.
- shortened the public search page and navigation label to `搜尋`; replaced its
  dataframe controls with the same borderless, whole-row detail links used by
  the performance ranking, while preserving the existing column order and
  sizing every column from whichever is wider, its heading or longest visible
  value on the current result page.
- shortened the comparison page and navigation label to `比較`, renamed its
  primary action to `開始比較`, moved the concise two-to-four ETF requirement
  below that action, and expanded the input from code-only entry to exact code,
  exact name or uniquely identifiable name keyword lookup; ambiguous keywords
  require a more complete entry rather than selecting an ETF by guesswork.
- shortened the planner holding-row action from `新增持股` to `持股`.
- removed private login from the sidebar, set the public navigation sidebar to
  start collapsed, and added a separate top-right `喵窩` action that opens a
  bordered token card in a native dialog; the original sidebar arrow and
  per-session owner access boundary remain unchanged.
- removed the extra vertical gap between the search result summary metrics and
  their existing divider.
- renamed every public-facing `歷史品質評等` label and related visible quality
  explanation to the GoodCat term `喵喵評等`, while preserving internal API
  field names and the A+ through F publication contract.
- moved each search and performance-ranking clear/reload pair directly below
  its primary action inside the same filter card, using a compact horizontal
  row aligned to the primary action; renamed the primary actions to `搜尋` and
  `篩選` respectively.
- removed the redundant `項目／內容` event table inside dividend expanders;
  expanding a summary row now leads directly to estimated and actual dividend
  composition details.
- renamed the first expanded composition heading to `現金股利組成`, reduced
  its public columns to composition, ratio and amount, removed `預估` from
  component descriptions, and retained e添富 as the official fallback when
  formal ACTUAL income composition is unavailable without relabelling the
  underlying data basis or formal income codes.
- consolidated the expanded composition into one selected table: complete
  formal rows take priority, otherwise one complete e添富 set is used; removed
  the separate `實際所得組成` block and prohibited cross-basis row mixing.
- retained dashed dividers between multiple payments in one annual dividend
  bar while removing dashed borders from the bar's four outside edges.
- placed the dividend color legend beside the `股利` heading, removed the
  redundant y-axis descriptions on both charts, and changed the yield heading
  to `殖利率(%)`.
- placed the `喵窩` action in the same native horizontal header row as the
  `GoodCat 股利喵` title on the home page and the `返回首頁` action on every
  other page, keeping it at the far right without a separate blank header row.
- recalibrated the desktop sidebar offset after the header change so its
  `首頁` row remains vertically aligned with `返回首頁`; mobile layout and the
  relative spacing of all navigation items remain unchanged.
- removed the legacy single-ETF `目標現金流分析` from the ETF detail journey;
  retained `稅務與再投入情境` as an owner-only `喵窩` tool until its role can
  be clarified against the portfolio tax calculation on the public planner.
- renamed the detail-page performance section to `績效`, replaced its technical
  price-return disclaimer with `資料來源於證交所`, inserted a broker-style
  line/area chart based only on saved official daily closes between the heading
  and source caption, and enclosed the complete period summary in a bordered
  card; fewer than two observations remain explicitly in a fetching state.
- converted the dividend summary to a bordered card, removed its event-count
  metric and repeated trend heading, and renamed the latest amount to
  `股利金額`; annual cash/stock dividends now use a stacked bar chart beside a
  separate annual-yield line chart, while unavailable stock-dividend data stays
  missing rather than being presented as zero.
- removed the redundant horizontal dividers between the detail identity,
  performance and dividend-summary cards, leaving card borders and natural
  spacing as the only visual separation.
- removed the technical `殖利率依據` column from the public dividend-history
  table while retaining its source and fallback fields in the API payload.
- merged the dividend summary list with the former duplicate history section:
  every five-field summary row is now expandable in place to reveal the same
  event and estimated/actual composition details, and the separate lower
  `配息歷史與組成` section is removed.
- shortened the paired chart labels to `股利` and `殖利率`, removed repeated
  x-axis titles, fixed both charts to the current five-year window, and stacked
  each distribution event with dashed segment borders so multiple payments in
  one year remain visible; the missing stock-dividend notice is owner-only.
- fixed the expandable dividend header and row columns to compact shared display
  widths with preserved whitespace and a monospace fallback; the shaded header
  reserves the disclosure-arrow gutter without horizontal scrolling. Renamed
  the card to `配息資料`, combined `現金/股票` without converting missing stock
  data to zero, derived a missing period from its ex-dividend calendar quarter,
  matched legend swatches to bar colors and hid the chart toolbars.
- narrowed `年/季`, renamed the final dividend-history column to `發放日`, and
  aligned every separator by fixed display width instead of variable tab stops.
- shortened the ETF detail title to `詳細資料`, removed the repeated query-code
  caption and placed the renamed `更新` action immediately to the right of the
  context-aware return action.
- tightened the ETF detail identity card while retaining a small top inset,
  moved management and asset type beside the code/name, removed the redundant
  core-data heading, and standardized the public badge as `喵喵評等：A+`～`F`
  or `喵喵評等：暫無`.
- reduced public unrated copy to `核心資料不足或未通過資料閘門`; detailed
  missing-evidence lines and missing master-data diagnostics now render only
  after the same browser session has successfully entered `喵窩`.
- aligned the desktop sidebar's `首頁` row with the main content's `返回首頁`
  action by shifting the complete navigation block as one unit; item order and
  relative spacing remain unchanged, and narrow/mobile layout is unaffected.
- hid the unrated `核心資料不足或未通過資料閘門` explanation from public
  detail views as well, while retaining it for verified `喵窩` sessions; detail
  page missing-value placeholders now consistently read `資料抓取中` instead
  of `尚無資料` or `歷史資料不足` without changing backend missing semantics.
- reduced the ETF detail code/name separator from a full-width space to one
  normal space while preserving the surrounding identity-card layout.
- standardized titled cards across public pages, including all titled ETF
  detail cards, to a `10px` top inset; untitled form, table and metric
  containers retain their existing spacing.
- removed the standalone detail-page ETF comparison heading and explanatory
  block; the shortened `加入比較` action now sits at the identity card's
  upper-right, aligns with the ETF code/name, uses the same unframed treatment
  as the return-home link and preserves the current ETF and return context.
- moved each search and performance-ranking clear/reload pair directly below
  its primary action inside the same filter card, using a compact horizontal
  row aligned to the primary action; renamed the primary actions to `搜尋` and
  `篩選` respectively.

Review focus:

- brand, slogan and GoodCat first impression;
- whether the planning action is immediately obvious;
- whether introductory copy is short and beginner-friendly;
- whether secondary exploration paths compete with the primary action;
- whether any public field should be removed, added or moved.

No page is accepted by automated tests alone. Owner feedback and the resulting
decision will be recorded here before moving to the next page.
