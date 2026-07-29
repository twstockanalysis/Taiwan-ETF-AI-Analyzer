### M5: FastAPI Backend

- FastAPI application factory
- System health endpoints
- API Router architecture
- ETF Repository
- ETF list and detail endpoints
- Keyword and ETF type filters
- Pagination
- API response validation
- Automated API tests
- Swagger API documentation


### M6: ETF Data Engine

- Evaluate official and public ETF data sources
- Define raw data import format
- Add ETF data validation
- Import ETF master records
- Update existing records safely
- Record import results and errors
- Replace development seed records


### M6: ETF Data Engine

- Official TWSE and TPEx source registry
- OpenAPI specification snapshots
- Official ETF master download
- Raw-data checksums and metadata
- ETF normalization and classification
- Processed and rejected data artifacts
- SQLite ETF master upsert
- Import batch records
- Data quality reports
- Automated pipeline tests


### M7: Streamlit Frontend

- Streamlit application shell
- FastAPI health check
- Configurable API base URL
- ETF keyword search
- Active and passive ETF filters
- Bond and non-bond filters
- ETF pagination
- ETF detail page
- Gregorian listing-date display
- Frontend API error handling
- Streamlit AppTest coverage


### M8: ETF Analysis Data

- Define ETF performance history schema
- Define dividend history schema
- Define dividend component schema
- Import official performance data
- Import official dividend data
- Store 76W distribution composition
- Add performance and dividend APIs
- Display analysis data on the website