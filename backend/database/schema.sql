-- Hearing test records
CREATE TABLE IF NOT EXISTS hearing_test (
    id TEXT PRIMARY KEY,
    test_date TIMESTAMP NOT NULL,
    test_time TIME,
    source_type TEXT NOT NULL CHECK(source_type IN ('audiologist', 'home')),
    location TEXT,
    device_name TEXT,
    technician_name TEXT,
    notes TEXT,
    image_path TEXT,
    ocr_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_test_date ON hearing_test(test_date DESC);

-- Audiogram measurements
CREATE TABLE IF NOT EXISTS audiogram_measurement (
    id TEXT PRIMARY KEY,
    id_hearing_test TEXT NOT NULL,
    ear TEXT NOT NULL CHECK(ear IN ('left', 'right')),
    frequency_hz INTEGER NOT NULL,
    threshold_db REAL NOT NULL,
    is_no_response BOOLEAN DEFAULT 0,
    measurement_type TEXT DEFAULT 'air_conduction',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_hearing_test) REFERENCES hearing_test(id),
    UNIQUE(id_hearing_test, ear, frequency_hz, measurement_type)
);

CREATE INDEX IF NOT EXISTS idx_measurement_lookup
    ON audiogram_measurement(id_hearing_test, ear, frequency_hz);

-- Saved test comparisons
CREATE TABLE IF NOT EXISTS test_comparison (
    id TEXT PRIMARY KEY,
    comparison_name TEXT,
    test_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to update modified_at
CREATE TRIGGER IF NOT EXISTS update_hearing_test_modtime
AFTER UPDATE ON hearing_test
BEGIN
    UPDATE hearing_test SET modified_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
