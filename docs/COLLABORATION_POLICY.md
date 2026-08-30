# 多人＋多 AI GitHub 協作規範

## 1. 目標

讓人類與多個 AI 可以平行協作，同時維持單一責任、可追溯決策、金融資料語意、安全邊界與可回復 Git 歷史。Issue 是需求來源，PR 是審查與合併來源，`AI_HANDOFF.md` 是未完成工作的即時交接來源。

## 2. 角色

- **Maintainer**：管理 repository、branch protection、labels、release、deploy、secrets 與最終 merge。
- **Human contributor**：認領 Issue、實作或擔任 AI sponsor，對需求與驗收負責。
- **Implementer AI**：在被授權範圍內讀取、修改、測試並整理證據；不能自行擴大範圍或核准自己。
- **Reviewer AI**：只讀檢查另一個實作者的 diff，提出可重現問題；不得直接合併，也不取代人類 reviewer。
- **Automation**：執行固定 CI／security gate；只有 workflow 結果本身可作為 required check。

每個 Issue 必須有一位人類 sponsor。沒有 sponsor 的 AI 工作只能做 read-only 分析或 Draft 提案。

## 3. 工作所有權與並行

1. 一個 Issue 只有一個 active implementer；大型 Issue 先拆成互不重疊的子 Issue。
2. 每位實作者使用自己的 branch 與 worktree。禁止兩個 AI 寫入同一工作樹或共同 force-push。
3. Issue 首則或進度留言列出 `Claimed scope`，包含檔案／模組及預計釋放時間。
4. 跨模組共用檔（schema、API model、navigation、global theme、requirements、migration）一次只由一個 branch 修改；其他工作以依賴 Issue 或 stacked PR 排隊。
5. 發現重疊時停止寫入，保留本地變更並由 sponsor 決定拆分、排序或重新指定 ownership。

## 4. AI 權限矩陣

| 等級 | 可執行 | 需要的授權 |
| --- | --- | --- |
| A0 讀取 | 搜尋、讀檔、檢查 git／CI 狀態、提出方案 | Issue 或使用者請求即可 |
| A1 本地實作 | 修改任務內檔案、執行測試、產生本地 diff | 明確要求實作 |
| A2 本地 Git | 建 branch/worktree、stage、commit | sponsor 明確授權或任務明確要求完成提交 |
| A3 GitHub 寫入 | push、建立／更新 Issue／PR、留言、上傳附件 | 確認 repository 與目的後取得明確授權 |
| A4 維護者操作 | merge、force-push、release、deploy、branch protection、secrets、正式資料 | AI 禁止；由人類 maintainer 執行 |

任何權限都不允許 AI 外傳 secrets、私人資料、瀏覽紀錄或未核准的本機檔案。權限只適用於當前任務，不會因先前曾獲准而永久延續。

## 5. Issue policy

- 先說明問題與使用者影響，再寫技術方案。
- 必填：scope、out of scope、acceptance criteria、資料語意、安全／隱私風險、依賴、AI 是否適合執行。
- 財稅公式、資料來源、schema、公開評等、認證及部署 Issue 標記 `risk:high`。
- 未確認需求的工作只能建立 `status:needs-decision` Issue，不得直接實作推測結果。

建議 labels：`type:feature`、`type:bug`、`type:data`、`type:docs`、`risk:high`、`status:ready`、`status:blocked`、`ai:allowed`、`ai:review-only`、`needs-human`。

## 6. PR policy

- PR 只能處理一個主要 Issue；超過一個可獨立回復的 concern 時拆 PR。
- 進行中使用 Draft。Ready 前完成 template、同步 base、清除未追蹤產物並附測試證據。
- AI 參與必須揭露：工具／代理、實作或審查角色、人類 sponsor、授權範圍及未由人類逐行確認的部分。
- Reviewer 只依 diff、測試及 contract 判斷；不得把 PR 描述當成已驗證事實。
- 重要留言必須由作者回覆並 resolve；禁止只用新的 AI 摘要掩蓋未解決討論。

## 7. Merge policy

`main` 應設定 branch protection：

- 禁止直接 push、force-push 與 branch deletion bypass；
- required pull request、required conversation resolution、required status checks；
- required checks 至少包含現有 `Security gate` 的 regression、secret scan、dependency audit 與 container security；
- 一般 PR 至少 1 位人類核准；高風險 PR 至少 2 位人類核准及 CODEOWNER；
- 新 commit 使舊核准失效；作者不可核准自己的 PR；AI 核准不計入門檻；
- 預設 squash merge 並自動刪除來源 branch；只有人類 maintainer 可按下 merge。

## 8. 交接與失敗恢復

AI／人員更換、工作暫停或權限受阻時，在 `AI_HANDOFF.md` 記錄精確 branch、base、commit、PR、claimed files、完成／未完成、測試及下一步。接手者必須重新驗證 GitHub 與工作樹狀態，不能依聊天記憶假定已 push 或 merge。

若 CI 失敗，先重現最小失敗並判斷是否由本 PR 引入；不得修改或跳過測試只為取得綠燈。若需要改 contract 或驗收條件，回到 Issue 取得人類決策。

## 9. GoodCat 專案特別 gate

- ACTUAL、e添富 fallback、76W、缺失與 0 的語意不可混用。
- 財稅、現金流、整數股數配置及品質評等變更必須有 deterministic tests 與可解釋輸出。
- 正式資料匯入需保留來源、日期及 review basis；AI 不能把未審核來源升格為正式資料。
- 公開 release 必須指定 exact commit，完成 SEC-4 後才可由人類 maintainer 宣告上線。
- 漏洞、憑證、認證繞過與外洩疑慮依 `SECURITY.md` 使用私密 Security Advisory，不得建立公開 Issue。

## 10. GitHub 設定清單

Maintainer 啟用本規範時應在 repository settings 完成：

- 保護 `main` 並套用上述 required reviews/checks；
- 啟用 CODEOWNERS review 與 stale approval dismissal；
- 禁止 bypass，僅保留緊急 maintainer break-glass，事後必須補 Issue／PR；
- 啟用自動刪除 merged branch、private vulnerability reporting、secret scanning、Dependabot alerts；
- 建立上述建議 labels；GitHub 不會因 Issue Form 引用 label 名稱而自動建立不存在的 label；
- 確認 Issue／PR template 已由 default branch 載入。
