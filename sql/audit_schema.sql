
CREATE TABLE IF NOT EXISTS etl_run_audit (
    run_id VARCHAR(100) PRIMARY KEY,
    dag_id VARCHAR(150),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,
    records_extracted INTEGER DEFAULT 0,
    records_transformed INTEGER DEFAULT 0,
    records_loaded INTEGER DEFAULT 0,
    raw_file_count INTEGER DEFAULT 0,
    error_message TEXT,
    CONSTRAINT valid_run_status
        CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED'))
);
