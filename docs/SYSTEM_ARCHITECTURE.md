# System Architecture

## Project Goal

TW ETF AI Analyzer is designed as a public Taiwan ETF
analysis website.

The first version focuses on data collection, ETF search,
performance ranking, dividend component analysis and
portfolio calculations.

AI recommendations will be developed after the first public
website version is completed.

## Application Architecture

```text
Web Browser
    |
    v
Frontend - Streamlit
    |
    v
Backend API - FastAPI
    |
    v
Service Layer
    |
    v
Database - SQLite