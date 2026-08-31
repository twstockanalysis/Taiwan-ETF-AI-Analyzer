# AI handoff

此檔是人類與多 AI 之間的 repository 內交接點。進入任務時先閱讀，離開、暫停、受阻或交給另一位實作者前更新。已合併或失效的內容移至對應 Issue／PR，主檔只保留目前有效交接。

## Active handoff

- Status: `WAITING_FOR_HUMAN_REVIEW`
- Issue: `#74` — https://github.com/twstockanalysis/goodcat-website/issues/74
- Owner / human sponsor: `GoodCat owner / current requester`
- Current implementer: `Codex /root`
- Branch: `data/74-detail-page-official-data`
- Base branch / commit: `main / 2d2d5f95fba52bac8b5cc191ed99fdf9291bf219`
- Latest implementation commit: `3e35f6b4a985b1102ec70dfe7c5dfff70ecd53c2`
- Pull request: Draft `#75` — https://github.com/twstockanalysis/goodcat-website/pull/75
- Last updated: `2026-08-31`

### Objective

完成 V5-1 第一輪詳細資料候選、覆蓋 ledger 與 frozen planner replay，提供
V5-2 owner 決策證據；不修改配置引擎或前端頁面。

### Claimed scope

- Files/modules: `backend/app/data_sources/`, `deployment/detail_data_candidate.py`,
  `deployment/v5_planner_replay.py`, V5 docs and related tests
- Do not touch: allocation services/objective, frontend layout/copy, source database,
  formal deployment, V4-8 and SEC-4

### Completed

- Verified `origin/main` baseline `2d2d5f9` contains PR #72 and #73.
- Created Issue #74 and switched to the dedicated data branch from exact main base.
- Added an isolated no-overwrite candidate builder, per-ETF visible-field coverage
  ledger, bond-inclusive price/performance refresh and cached official-price yield fallback.
- Built candidate SHA `64a4ab5f947777b39e38edf90146db597512a2dad42f7a31edcab894331b10e5`;
  integrity `ok`, foreign-key violations `0`.
- Replayed four frozen planner cases and visually reviewed actual Streamlit detail and
  public-planner results against the candidate database.
- Recorded first-round coverage, result delta and V5-3 priorities in
  `docs/V5_1_DATA_EVIDENCE.md`.

### Remaining

- Owner/CODEOWNER and a second human review Draft PR #75; AI must not merge it.
- Owner decides whether to accept V5-1 evidence and begin V5-3; V5-2 findings do not
  authorize algorithm or page changes.

### Validation evidence

- Candidate pipeline: 261 ETF master rows; official price history 231／261; 1M／3M／
  6M／1Y coverage 230／223／210／190; dividend yield 113／261; ACTUAL 76W 1／261.
- Planner: zero holdings 47 eligible and `TARGET_MET`; all frozen one／N holding cases
  remain 0 eligible because constituent overlap data is unavailable.
- Targeted V5 tests: 21 tests in 14.849s, all passed.
- Compileall: passed for `backend frontend tests deployment`.
- Full regression: 1,047 tests in 485.833s, all passed; only existing Streamlit
  bare-mode／Arrow auto-conversion warnings were emitted.
- `git diff --cached --check`: passed before commit.
- Implementation commit `3e35f6b` pushed; Draft PR #75 created.

### Decisions and invariants

- V5 order is data round 1 -> result review 1 -> result-driven data round 2 -> result review 2 -> closeout.
- V4-8, formal deployment and SEC-4 remain paused through V5-5.
- First data round freezes the allocation engine and accepted page layout.
- Missing official data remains unavailable; estimated capital gain never becomes formal 76W.

### Risks or blockers

- This is high-risk official-data work and the Draft PR requires CODEOWNER and two human
  approvals before a human maintainer may merge.
- Candidate artifacts and database are local/ignored and must not be committed.
- Fund size, expense ratio, distribution period, stock dividend, broader ACTUAL evidence,
  constituent overlap and adjusted long-term history remain incomplete.

### Next safe action

Review Draft PR #75 and decide the V5-3 data priority; do not merge without required
human approvals, deploy, resume V4-8 or sign SEC-4.

## 更新規則

1. 使用精確 commit SHA、branch、Issue／PR 連結，不寫「最新」或「剛才」。
2. 區分「已修改」「已 commit」「已 push」「已建立 PR」「已 merge」；不得用「完成」概括不同狀態。
3. 記錄未執行的測試及原因，不把局部測試描述成完整回歸。
4. 列出目前占用的檔案；接手者確認工作樹與遠端狀態後才可清除 claimed scope。
5. 不在此檔放 token、帳號、cookie、正式資料或本機密鑰路徑。
