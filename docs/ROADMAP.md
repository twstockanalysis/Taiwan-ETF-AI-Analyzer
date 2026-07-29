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

#### Completed

- Performance, dividend and component schemas
- Flexible 76W component model
- TWSE historical closing-price source
- Daily price normalization
- Six-month market-price return calculator
- Batch non-bond ETF performance pipeline
- Performance SQLite upsert
- Latest six-month performance ranking
- Insufficient-history and per-ETF error handling
- Processed, rejected and quality-report files
- Automated Repository and Pipeline tests

#### Next

- Six-month performance ranking API
- Dividend event source discovery
- Dividend history import
- 76W component import
- Performance and dividend website pages

### M8-2B-R1A Completed

- Added ETF performance metric types
- Added PRICE_RETURN, TOTAL_RETURN and NAV_RETURN definitions
- Added safe SQLite performance-table migration
- Migrated existing performance records to PRICE_RETURN
- Added reusable multi-period price-return calculator
- Added 1M, 3M, 6M and 1Y calculations
- Preserved six-month pipeline compatibility
- Updated repository uniqueness and ranking filters
- Added migration and multi-period tests