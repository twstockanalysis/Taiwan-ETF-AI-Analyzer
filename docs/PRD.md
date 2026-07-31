# Product Requirements

## Product

TW ETF AI Analyzer is a public Taiwan ETF analysis website.

## Primary users

Users who want to:

- Search and classify Taiwan ETFs
- Compare recent market-price performance
- Review dividend events and composition
- Distinguish estimated gains from official `76W`
- Understand data completeness before making a decision

## Core principles

1. Official data and traceable provenance have priority.
2. Missing data is never silently converted to zero.
3. Different performance periods and metric definitions are not mixed.
4. Estimated composition is not presented as actual tax-source composition.
5. The public frontend accesses data only through FastAPI.
6. Automated tests protect schema, API and frontend contracts.

## M8 delivered scope

- ETF master search and detail
- 1M, 3M, 6M and 1Y price-return ranking
- Dividend history and component display
- ACTUAL `76W` handling
- Source-document retention
- Actual-dividend coverage and review queue
- Streamlit data-quality page

## Next product priorities

M9 — completed:

- Navigation, URL state and performance-ranking information order
- FastAPI-backed homepage system overview
- ETF detail sections and data freshness
- 2–4 ETF comparison with URL state and data completeness
- Shared formatters, classification labels, clickable rows, pagination and states

M10–M11 — next:

- Multi-period performance display with 6M as the default preference
- Responsive typography that preserves visible values with the sidebar open
- Income-allocation and combination analysis
- Explainable recommendation and decision workflows
- Manual holdings and Excel export

M12:

- Scheduled data updates
- Monitoring, backups and public deployment

## Out of current core scope

- Broker login or account synchronization
- Automatic order placement
- Fugle or Shioaji integration
- Mobile native applications
- Unverified scraping
- OCR-based automatic tax-code inference

External APIs can be evaluated only after the core website and deployment
architecture are complete.
