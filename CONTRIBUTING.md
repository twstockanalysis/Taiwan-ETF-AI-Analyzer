# Contributing to GoodCat 股利喵

歡迎人類開發者與 AI 輔助工具共同參與。開始前請閱讀 `AGENTS.md`、`docs/COLLABORATION_POLICY.md` 與相關產品／計算 contract。

## 標準流程

1. 先建立或認領 Issue，寫清楚問題、範圍、驗收條件與風險級別。
2. 從最新 `main` 建立單一用途 branch；不要多人或多 AI 共用可寫 branch。
3. 在 Issue 留下 claimed scope；需要轉交時更新 `AI_HANDOFF.md`。
4. 實作、補測試及文件，保持 ACTUAL／估算／缺失／0 的語意區隔。
5. 先開 Draft PR 取得早期意見；完成 PR template 後才標記 Ready for review。
6. CI 全綠且取得所需人類核准後，由人類維護者 squash merge。

## Branch naming

全部使用小寫英數與連字號；`<issue>` 使用 GitHub Issue 編號，無 Issue 的純文件初始化可使用明確 scope。

- `feature/<issue>-<slug>`：新功能
- `fix/<issue>-<slug>`：錯誤修正
- `data/<issue>-<slug>`：資料來源、pipeline 或 coverage
- `docs/<issue-or-scope>-<slug>`：文件與協作制度
- `test/<issue>-<slug>`：只調整測試
- `security/<sec-id>-<slug>`：獨立資安工作
- `chore/<issue-or-scope>-<slug>`：維護工作
- `ai/<agent>/<type>-<issue>-<slug>`：需清楚標示 AI 獨立工作區時使用

禁止含糊名稱，例如 `update`、`test2`、`ai-fix`；禁止直接推送 `main`。

## Commit

格式：`<type>: <imperative summary>`，常用 type 為 `feat`、`fix`、`data`、`docs`、`test`、`security`、`chore`。

每個 commit 應可獨立理解與回復；不要混入格式化全專案、產生檔、個人設定或其他 Issue 的內容。

## Review and merge

- 一般變更：至少一位非作者人類核准。
- 高風險變更：至少兩位人類核准，其中一位為 CODEOWNER。包含認證／授權、資安、部署、database schema／migration、財稅與配置計算、正式資料來源及公開評等 contract。
- AI review 是補充證據，不計入人類核准數。
- 所有 required checks 必須成功，對話需 resolved，branch 不得落後 base。
- 預設 squash merge；merge commit 只用於維護者核准的多提交歷史，禁止 AI 自行 merge 或 force-push。

## Local validation

依變更範圍執行針對性測試。準備 PR 時至少執行：

```powershell
.venv\Scripts\python.exe -m compileall -q backend frontend tests deployment
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
git diff --check
```

若無法執行，必須在 PR 的「未執行驗證」說明原因與風險。
