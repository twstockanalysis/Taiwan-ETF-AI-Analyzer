-- TW ETF AI Analyzer
-- SQLite database schema

CREATE TABLE IF NOT EXISTS etf_master (
    code TEXT PRIMARY KEY,

    name TEXT NOT NULL,

    is_active INTEGER NOT NULL DEFAULT 0
        CHECK (is_active IN (0, 1)),

    is_bond INTEGER NOT NULL DEFAULT 0
        CHECK (is_bond IN (0, 1)),

    listing_date TEXT,

    fund_size REAL
        CHECK (fund_size IS NULL OR fund_size >= 0),

    expense_ratio REAL
        CHECK (
            expense_ratio IS NULL
            OR (
                expense_ratio >= 0
                AND expense_ratio <= 100
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_etf_master_name
ON etf_master (name);


CREATE TABLE IF NOT EXISTS import_batch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    pipeline_name TEXT NOT NULL,

    source_id TEXT NOT NULL,

    endpoint_id TEXT NOT NULL,

    started_at TEXT NOT NULL,

    completed_at TEXT,

    status TEXT NOT NULL
        CHECK (
            status IN (
                'running',
                'success',
                'failed'
            )
        ),

    raw_record_count INTEGER NOT NULL DEFAULT 0
        CHECK (raw_record_count >= 0),

    accepted_record_count INTEGER NOT NULL DEFAULT 0
        CHECK (accepted_record_count >= 0),

    rejected_record_count INTEGER NOT NULL DEFAULT 0
        CHECK (rejected_record_count >= 0),

    inserted_record_count INTEGER NOT NULL DEFAULT 0
        CHECK (inserted_record_count >= 0),

    updated_record_count INTEGER NOT NULL DEFAULT 0
        CHECK (updated_record_count >= 0),

    deleted_development_record_count INTEGER NOT NULL DEFAULT 0
        CHECK (deleted_development_record_count >= 0),

    checksum_sha256 TEXT,

    raw_snapshot_path TEXT,

    processed_snapshot_path TEXT,

    rejected_snapshot_path TEXT,

    quality_report_path TEXT,

    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_import_batch_status
ON import_batch (status);

CREATE INDEX IF NOT EXISTS idx_import_batch_started_at
ON import_batch (started_at);

-- ============================================================
-- ETF 績效資料
-- ============================================================

CREATE TABLE IF NOT EXISTS etf_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    etf_code TEXT NOT NULL,

    as_of_date TEXT NOT NULL,

    period_code TEXT NOT NULL
        CHECK (
            period_code IN (
                '1D',
                '1W',
                '1M',
                '3M',
                '6M',
                '1Y',
                '3Y',
                '5Y'
            )
        ),

    metric_code TEXT NOT NULL
        DEFAULT 'PRICE_RETURN'
        CHECK (
            metric_code IN (
                'PRICE_RETURN',
                'TOTAL_RETURN',
                'NAV_RETURN'
            )
        ),

    return_pct REAL NOT NULL
        CHECK (return_pct >= -100),

    source_id TEXT NOT NULL
        CHECK (length(trim(source_id)) > 0),

    import_batch_id INTEGER,

    source_updated_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (etf_code)
        REFERENCES etf_master (code)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (import_batch_id)
        REFERENCES import_batch (id)
        ON DELETE SET NULL,

    UNIQUE (
        etf_code,
        as_of_date,
        period_code,
        metric_code,
        source_id
    )
);


CREATE INDEX IF NOT EXISTS
idx_etf_performance_lookup
ON etf_performance (
    metric_code,
    period_code,
    as_of_date DESC,
    return_pct DESC
);


CREATE INDEX IF NOT EXISTS
idx_etf_performance_code_date
ON etf_performance (
    etf_code,
    metric_code,
    period_code,
    as_of_date DESC
);


-- ============================================================
-- ETF 配息事件
-- ============================================================

CREATE TABLE IF NOT EXISTS etf_dividend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    etf_code TEXT NOT NULL,

    source_event_id TEXT NOT NULL
        CHECK (
            length(trim(source_event_id)) > 0
        ),

    announcement_date TEXT,

    ex_dividend_date TEXT,

    record_date TEXT,

    payment_date TEXT,

    amount_per_unit REAL NOT NULL
        CHECK (amount_per_unit >= 0),

    currency TEXT NOT NULL
        DEFAULT 'TWD'
        CHECK (length(currency) = 3),

    source_id TEXT NOT NULL
        CHECK (length(trim(source_id)) > 0),

    import_batch_id INTEGER,

    source_updated_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        announcement_date IS NOT NULL
        OR ex_dividend_date IS NOT NULL
        OR record_date IS NOT NULL
        OR payment_date IS NOT NULL
    ),

    CHECK (
        ex_dividend_date IS NULL
        OR payment_date IS NULL
        OR payment_date >= ex_dividend_date
    ),

    FOREIGN KEY (etf_code)
        REFERENCES etf_master (code)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (import_batch_id)
        REFERENCES import_batch (id)
        ON DELETE SET NULL,

    UNIQUE (
        source_id,
        source_event_id
    )
);


CREATE INDEX IF NOT EXISTS
idx_etf_dividend_code_payment
ON etf_dividend (
    etf_code,
    payment_date DESC
);


CREATE INDEX IF NOT EXISTS
idx_etf_dividend_ex_date
ON etf_dividend (
    ex_dividend_date DESC
);


-- ============================================================
-- ETF 每期配息組成
-- ============================================================

CREATE TABLE IF NOT EXISTS etf_dividend_component (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    dividend_id INTEGER NOT NULL,

    component_code TEXT NOT NULL
        CHECK (
            length(trim(component_code)) > 0
        ),

    component_basis TEXT NOT NULL
        DEFAULT 'ACTUAL'
        CHECK (
            component_basis IN (
                'ESTIMATED',
                'ACTUAL'
            )
        ),

    component_name TEXT,

    amount_per_unit REAL,

    ratio_pct REAL,

    source_id TEXT NOT NULL
        CHECK (length(trim(source_id)) > 0),

    import_batch_id INTEGER,

    source_updated_at TEXT,

    created_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        amount_per_unit IS NOT NULL
        OR ratio_pct IS NOT NULL
    ),

    CHECK (
        amount_per_unit IS NULL
        OR amount_per_unit >= 0
    ),

    CHECK (
        ratio_pct IS NULL
        OR (
            ratio_pct >= 0
            AND ratio_pct <= 100
        )
    ),

    FOREIGN KEY (dividend_id)
        REFERENCES etf_dividend (id)
        ON DELETE CASCADE,

    FOREIGN KEY (import_batch_id)
        REFERENCES import_batch (id)
        ON DELETE SET NULL,

    UNIQUE (
        dividend_id,
        component_basis,
        component_code,
        source_id
    )
);


CREATE INDEX IF NOT EXISTS
idx_etf_dividend_component_code
ON etf_dividend_component (
    component_code,
    ratio_pct DESC
);
