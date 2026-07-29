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


### M8: ETF Analysis Data — In Progress

#### M8-1 Completed

- ETF performance schema
- ETF dividend-event schema
- ETF dividend-component schema
- Six-month performance data contract
- Flexible 76W component data contract
- Schema constraints and automated tests

#### Next

- Official performance-source discovery
- Official dividend-source discovery
- Performance and dividend import pipelines
- Performance and dividend APIs
- Website analysis pages