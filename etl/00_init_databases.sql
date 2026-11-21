-- 1. Drop stale databases from previous project track (clean slate)
DROP DATABASE IF EXISTS olist_bronze;
DROP DATABASE IF EXISTS olist_silver;
DROP DATABASE IF EXISTS olist_gold;
DROP DATABASE IF EXISTS olist_audit;

-- 2. Create fresh Medallion isolation databases
CREATE DATABASE olist_bronze CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE olist_silver CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE olist_gold   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE olist_audit  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. Create Audit Telemetry Table to track every ingestion run
CREATE TABLE olist_audit.etl_run_log (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    layer VARCHAR(20) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    row_count INT NOT NULL,
    column_count INT NOT NULL,
    total_null_cells INT NOT NULL,
    duration_sec DECIMAL(8, 2),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);