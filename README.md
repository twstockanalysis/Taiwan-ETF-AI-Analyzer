# GoodCat 股利喵

多人與多 AI 協作請先閱讀 [`CONTRIBUTING.md`](CONTRIBUTING.md)、[`AGENTS.md`](AGENTS.md) 與 [`docs/COLLABORATION_POLICY.md`](docs/COLLABORATION_POLICY.md)。進行中的 AI 工作以 [`AI_HANDOFF.md`](AI_HANDOFF.md) 為 repository 內交接來源。

## Project introduction

GoodCat 股利喵是為 ETF 初學者設計的台灣 ETF 現金流規劃網站。V3 將從使用者的領息目標、指定月份與 0～N 檔現有持股出發，提供透明的 ETF、整數股數與所需資金配置情境。

Main function:
- ETF performance analysis
- 76W analysis
- dividends for every months
- Explainable allocation fit and risks
- Excel Dashboard
---
## Author
TU
---
## Develop enviroment
- Python
- VS Code
- GitHub
---
## ETF API
Start the development server:
```powershell
python -m uvicorn backend.app.main:app --reload
---
## Update ETF Master Data
Run the complete official data pipeline:
```powershell
python -m backend.app.data_sources.etf_master_pipeline
---
## Streamlit Website
Start the FastAPI backend:
```powershell
python -m uvicorn backend.app.main:app --reload
```
Start the Streamlit frontend in another terminal:
```powershell
python -m streamlit run frontend/app.py
```
Open the website:
```text
http://localhost:8501
```
Current website features:

- FastAPI health status
- ETF keyword search
- Active and passive ETF filters
- Bond and non-bond filters
- ETF pagination
- ETF detail page
- Gregorian listing dates
- Frontend connection error handling
