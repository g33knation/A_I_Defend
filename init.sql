CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
