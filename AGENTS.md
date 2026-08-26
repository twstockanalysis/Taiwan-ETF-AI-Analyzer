# GoodCat 股利喵 — Codex Instructions

## Project Goal

建立可公開使用、以 ETF 初學者為核心使用者的台灣 ETF 現金流配置網站「GoodCat 股利喵」。

第一版網站完成前，專案重點是：

- ETF 基本資料查詢
- ETF 績效排名
- 配息組成與 76W 分析
- 月月領息資料呈現
- 持股計算
- Excel 匯出
- 公開網站部署

V3 的核心是從現金流目標、領息月份及 0～N 檔現有持股出發，自動產生透明的 ETF 與整數股數配置結果。V4 將 ETF 歷史品質與主人目標的配置適配結果分開呈現；前台可顯示版本化的 `A+`～`F` 品質評等，但不得顯示原始分數、內部排名或評定可信度，缺少核心資料時必須顯示暫不評等。

真實網域部署與 SEC-4 `READY` 延後到 V4 功能及逐頁體驗驗收完成後；SEC-4 仍是正式公開上線前不可略過的 gate。

## Architecture

```text
Browser
    |
    v
Streamlit Frontend
    |
    v
FastAPI Backend
    |
    v
Service / Repository Layer
    |
    v
SQLite Database
