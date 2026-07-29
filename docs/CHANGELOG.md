##2026/7/28
### Added

- ETF list pagination
- ETF keyword search
- Active ETF filtering
- Bond ETF filtering
- ETF list response metadata
- API parameter validation
- Automated filtering and pagination tests

### Changed

- ETF list API now returns a paginated response object
- ETF Repository now supports dynamic filtering


##2026/7/29 morning
### Added

- End-to-end ETF master update pipeline
- Import batch database table
- Success and failure batch tracking
- ETF data quality reports
- Rejection reason summaries
- Pipeline-level automated tests

### Changed

- ETF master download, normalization and import can now run
  through one command


##2026/7/29 afternoon
### Added

- Streamlit frontend application
- FastAPI connection status
- ETF search and filtering page
- ETF pagination controls
- Hidden ETF detail page
- ETF detail query parameter navigation
- Streamlit AppTest coverage
- Frontend documentation

### Changed

- ETF listing dates are normalized and displayed using the
  Gregorian ISO 8601 format
- The website frontend obtains all ETF data through FastAPI

### Fixed

- Seven-digit ROC listing dates are no longer interpreted as
  Gregorian years
- ETF 0050 listing date now displays as 2003-06-30