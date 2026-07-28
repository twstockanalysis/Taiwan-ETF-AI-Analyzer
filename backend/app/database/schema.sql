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