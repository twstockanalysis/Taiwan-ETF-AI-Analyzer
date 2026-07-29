# ETF Analysis Data

## Purpose

Milestone 8 adds time-varying ETF analysis data.

ETF analysis data must not be stored directly in `etf_master`.

## Data Tables

### etf_performance

Stores ETF performance snapshots by:

- ETF code
- Data date
- Performance period
- Return percentage
- Source
- Import batch

Supported periods:

```text
1D
1W
1M
3M
6M
1Y
3Y
5Y
```

The six-month period is the primary period used by the first
recommendation-ranking model.

### etf_dividend

Stores one record for each ETF distribution event.

Possible dates include:

- Announcement date
- Ex-dividend date
- Record date
- Payment date

Every event includes:

- Distribution amount per unit
- Currency
- Source event identifier
- Source and import batch

### etf_dividend_component

Stores the source composition of one distribution event.

Examples of source component codes may include:

```text
54C
76W
```

The database preserves the source code and source description.

It does not infer the meaning of a code solely from its spelling.

## 76W Analysis

`76W` is stored as a normal distribution component:

```text
component_code = 76W
```

Possible values include:

```text
amount_per_unit
ratio_pct
```

A distribution may contain multiple component records.

The application can later calculate:

- 76W ratio for one distribution
- Average 76W ratio
- Latest 76W ratio
- Percentage of distributions with 100% 76W
- Six-month performance combined with 76W quality

## Data Integrity

Performance uniqueness:

```text
ETF + date + period + source
```

Dividend-event uniqueness:

```text
source + source event ID
```

Dividend-component uniqueness:

```text
dividend event + component code
```

Deleting an ETF deletes its performance and dividend history.

Deleting a dividend event deletes all associated components.

## Source Policy

Official or explicitly permitted data sources have priority.

HTML pages must not be scraped when their terms prohibit
unauthorized automated retrieval.

Source component codes and descriptions must be stored before
the project applies analytical classifications.