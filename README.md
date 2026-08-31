# GoodCat 股利喵

## Project introduction

GoodCat 股利喵 is a Taiwan ETF cash-flow planning website for ETF beginners.
Users start with a dividend-income target, selected payment months, and zero or
more existing ETF holdings. The website produces transparent scenarios that
show ETF selections, whole-share quantities, required capital, assumptions,
risks, limitations, and exclusion reasons.

## Main features

- ETF search, detail, comparison, and performance analysis
- Dividend-event and dividend-yield history
- Formal ACTUAL dividend-composition evidence and clearly labeled estimated fallback data
- Explainable whole-share cash-flow allocation scenarios
- Monthly after-tax cash-flow, tax, reinvestment, and long-term projections
- Excel decision exports

The website does not place orders or provide buy or sell instructions. Missing
official data remains unavailable instead of being converted to zero.

## Author

TU

## Development environment

- Python
- FastAPI
- Streamlit
- SQLite
- Visual Studio Code
- GitHub

## FastAPI backend

Start the development API:

```powershell
python -m uvicorn backend.app.main:app --reload
```

The local API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## ETF master data

Run the official ETF master-data pipeline:

```powershell
python -m backend.app.data_sources.etf_master_pipeline
```

## Streamlit website

Start the FastAPI backend first, then start the Streamlit frontend in another
terminal:

```powershell
python -m streamlit run frontend/app.py
```

Open the website at:

```text
http://127.0.0.1:8501
```

## Validation

Run the standard pre-PR validation from the project virtual environment:

```powershell
.venv\Scripts\python.exe -m compileall -q backend frontend tests deployment
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
git diff --check
```
