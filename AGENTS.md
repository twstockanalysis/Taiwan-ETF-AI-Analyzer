# GoodCat 股利喵 — AI 協作規則

本檔適用於整個 repository。所有 AI 助理、代理與自動化工具開始工作前都必須閱讀；完整制度見 [`docs/COLLABORATION_POLICY.md`](docs/COLLABORATION_POLICY.md)，中斷或轉交工作時更新 [`AI_HANDOFF.md`](AI_HANDOFF.md)。

## 產品與架構

GoodCat 股利喵是面向 ETF 初學者的台灣 ETF 現金流規劃網站。架構為 Streamlit frontend → FastAPI backend → service/repository → SQLite。

- 結果必須透明、可解釋，呈現假設、理由、限制、估算、風險與排除原因。
- 不提供買賣指令，不把品質評等當成個人適配結論。
- ACTUAL 正式配息組成缺失時必須維持缺失；不得把缺失當成 0，也不得把 e添富估計資本利得改稱正式 `76W`。
- 公開部署前仍須通過 SEC-4；任何 AI 不得自行宣布正式上線或 `READY`。

## 開始工作前

1. 閱讀 Issue、相關 PRD／contract、`AI_HANDOFF.md` 與目前 `git status`。
2. 確認 branch、base、既有 PR、未提交變更及負責範圍；不得假定前一位 AI 的變更已提交、推送或合併。
3. 一個 Issue 對應一個主要 branch 與一位當前實作者；多 AI 同時工作時，各自使用獨立 branch/worktree，不共用可寫工作樹。
4. 先標示預計修改的檔案／模組。若與其他人的 claimed scope 重疊，先停止並協調。

## AI 權限

- 預設允許：讀檔、搜尋、不改變外部狀態的檢查、任務範圍內本地修改與測試。
- 需要人類明確授權：建立／切換共享 branch、commit、push、建立或修改 PR／Issue、對外留言、上傳檔案、改動 GitHub 設定。
- 禁止自行執行：merge、force-push、改寫他人歷史、刪除遠端 branch、release、正式部署、SEC-4 簽核、變更 secrets／權限、操作正式資料庫或真實帳戶。
- AI review 不能取代人類核准；作者 AI 不得扮演自己的核准者。
- 不得輸出、提交或轉傳 token、cookie、個資、未匿名化正式資料、瀏覽紀錄或本機密鑰。

## 實作與驗證

- 保留使用者及其他協作者的既有變更；禁止使用 `git reset --hard`、任意 checkout 覆蓋或未確認的批次刪除。
- 計算、API 與資料語意變更必須同步測試與 contract／API 文件。
- Streamlit 變更遵守已安裝版本的官方做法；不得新增 deprecated `components.v1`、`use_container_width` 或不必要的 HTML/CSS workaround。
- 至少執行針對性測試。高風險或準備 PR 時執行：

```powershell
.venv\Scripts\python.exe -m compileall -q backend frontend tests deployment
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

- 提交前執行 `git diff --check`，確認沒有 secrets、database、log、暫存檔或無關產物。

## Git 與 PR

- branch 依 `CONTRIBUTING.md` 命名；禁止直接在 `main` 開發或推送。
- commit 要小而可回復，使用 `<type>: <imperative summary>`，不可混入不相關修正。
- PR 必須連結 Issue，填完測試、風險、資料語意、AI 參與及交接欄位；進行中預設使用 Draft PR。
- `main` 只接受 PR；CI 全綠、branch 已同步、至少一位非作者人類核准後，才能由人類維護者 squash merge。
- 資安、認證、部署、schema／migration、財稅計算與正式資料來源變更需要 CODEOWNER 且至少兩位人類核准。

## 交接

工作未完成、需要換人或等待外部決策時，立即更新 `AI_HANDOFF.md`：記錄目標、branch／commit、已完成、未完成、測試、已知風險、claimed files 與下一個安全步驟。不得只留下聊天摘要。
