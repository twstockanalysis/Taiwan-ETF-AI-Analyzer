# TW ETF AI Analyzer — Codex Instructions

## Project Goal

建立可公開使用的台灣 ETF 分析網站。

第一版網站完成前，專案重點是：

- ETF 基本資料查詢
- ETF 績效排名
- 配息組成與 76W 分析
- 月月領息資料呈現
- 持股計算
- Excel 匯出
- 公開網站部署

AI 評分、AI 投資組合與決策平台，等第一版公開網站完成後再開發。

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