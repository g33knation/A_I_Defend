CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  source TEXT,
  type TEXT,
  payload JSONB,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS detections (
  id SERIAL PRIMARY KEY,
  event_id INT REFERENCES events(id),
  summary TEXT,
  score REAL,
  adjusted_score REAL,
  category TEXT,
  ai_output JSONB,
  created_at TIMESTAMP DEFAULT now(),
  feedback TEXT
);
