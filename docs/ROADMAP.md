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

### M8-2B-R1B Completed

- Added multi-period performance pipeline
- Added 1M, 3M, 6M and 1Y pipeline selection
- Reused one price download across all requested periods
- Added automatic 3, 5, 8 and 14 month download ranges
- Included recently listed ETFs in short-period calculations
- Added period-specific coverage reporting
- Preserved the legacy six-month pipeline interface
- Added ranking CLI period selection
- Added multi-period pipeline and CLI tests

### M8-2C Completed

- Added performance ranking API
- Added period and metric query validation
- Added active and bond filters
- Added ranking pagination and global rank numbers
- Added single-ETF multi-period performance API
- Added latest-record-per-period repository query
- Added empty-performance and missing-ETF handling
- Added OpenAPI and FastAPI integration tests

### M8-2D Completed

- Added frontend performance API clients
- Added the Streamlit performance-ranking page
- Added 1M, 3M, 6M and 1Y period selection
- Added active, passive and bond filters
- Added ranking pagination
- Added fully clickable ranking rows
- Added multi-period performance to ETF detail pages
- Added explicit insufficient-history display
- Added API-client, UI-helper and AppTest coverage
- Fixed ETF clickable-row test discovery

### M8-3A-1 Completed

- Added the TWSE ETF e添富 dividend source
- Added official HTML download and raw snapshots
- Added ROC-to-Gregorian dividend date parsing
- Added dividend-event normalization
- Added five estimated distribution components
- Kept estimated realized capital gains separate from 76W
- Added source and normalization tests

### M8-3A-2 Completed

- Added dividend-component basis migration
- Migrated legacy component rows to ACTUAL
- Added basis-aware and source-aware component uniqueness
- Added dividend-event upsert
- Added dividend-component upsert
- Added atomic event-and-component imports
- Added clear missing-ETF and missing-event validation
- Added dividend event and component query functions
- Added migration and Repository tests

### M8-3B Completed

- Added the formal TWSE ETF dividend import pipeline
- Added HTML raw snapshots and import-batch tracking
- Added processed dividend-event and component artifacts
- Added rejected-event artifacts with rejection categories
- Added missing ETF-master filtering without whole-batch failure
- Added atomic dividend event and component upserts
- Added dividend quality reports and coverage statistics
- Added explicit ESTIMATED versus ACTUAL policy enforcement
- Prevented estimated realized capital gains from becoming 76W
- Added idempotency, failure-state and quality-report tests

### M8-3C Completed

- Added ETF dividend-history API
- Added dividend-history pagination and totals
- Added single-dividend detail API
- Added component basis, code and source filters
- Added actual 76W history API
- Kept estimated realized capital gains outside 76W statistics
- Preserved null semantics when actual 76W data is unavailable
- Added dividend query Repository functions
- Added OpenAPI, Repository and FastAPI tests

### M8-3D Completed

- Added frontend dividend API clients
- Added ETF dividend-event summary
- Added actual 76W summary metrics
- Added expandable dividend history
- Added estimated and actual component sections
- Kept estimated realized capital gains separate from 76W
- Preserved missing-data versus disclosed-zero semantics
- Kept dividend API failures isolated from the rest of the detail page
- Added API-client and Streamlit AppTest coverage

### M8-4A Completed

- Added human-reviewed actual dividend JSON input
- Added strict ACTUAL-only source policy
- Added official tax-source code normalization
- Rejected EST_ codes from the actual import path
- Added ETF, ex-date and amount event matching
- Added record-date and payment-date verification
- Rejected missing and ambiguous dividend-event matches
- Added atomic ACTUAL component upsert
- Added raw, processed, rejected and quality-report artifacts
- Preserved source document ID, URL and date in audit artifacts
- Added import-batch success and failure tracking
- Added model, matcher and pipeline tests
- Kept estimated realized capital gains separate from 76W

### M8-4B Completed

- Added formal actual-dividend source Registry
- Added source modes and explicit retrieval policies
- Added dividend source-document audit table
- Added idempotent source-document Migration
- Added SHA-256 content-addressed HTML snapshots
- Added official-domain and HTTPS validation
- Added source-document version retention
- Added downloaded, parsed, rejected and failed states
- Added the first verified Cathay actual-dividend adapter
- Required explicit actual-composition wording
- Rejected estimated-composition wording
- Preserved official 76W and 54C codes and descriptions
- Reused the M8-4A event matcher and ACTUAL component import
- Kept network retrieval explicit rather than automatic
- Added source, repository, adapter and pipeline tests

### M8-4C Completed

- Added actual-dividend event coverage calculations
- Added estimated, ACTUAL, ACTUAL 76W and source-document counts
- Preserved missing-data versus formally disclosed zero semantics
- Kept estimated realized capital gains outside 76W coverage
- Added the dividend source-review queue
- Added pending, in-review, resolved and skipped states
- Prevented duplicate queue items by event and issue type
- Added automatic resolution when missing data is supplied
- Preserved skipped items while their issue remains unresolved
- Added coverage and queue quality-report artifacts
- Added read-only data-quality API endpoints
- Added Migration, Repository, Pipeline and API tests
