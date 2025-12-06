CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    summary TEXT,
    score FLOAT,
    adjusted_score FLOAT,
    category VARCHAR(50),
    ai_output JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detection_feedback (
    id SERIAL PRIMARY KEY,
    detection_id INTEGER REFERENCES detections(id),
    feedback VARCHAR(50), -- 'true_positive', 'false_positive'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_detections_created_at ON detections(created_at);
