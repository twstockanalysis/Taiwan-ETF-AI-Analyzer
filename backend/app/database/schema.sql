-- TW ETF AI Analyzer
-- SQLite database schema

CREATE TABLE IF NOT EXISTS etf_master (
    code TEXT NOT NULL PRIMARY KEY,

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