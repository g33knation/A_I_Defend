-- Create events table
CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  source TEXT,
  type TEXT,
  payload JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- Create detections table
CREATE TABLE IF NOT EXISTS detections (
  id SERIAL PRIMARY KEY,
  event_id INT REFERENCES events(id) ON DELETE CASCADE,
  summary TEXT,
  score REAL,
  adjusted_score REAL,
  category TEXT,
  ai_output JSONB,
  created_at TIMESTAMP DEFAULT now(),
  feedback TEXT
);

-- Create detection_feedback table
CREATE TABLE IF NOT EXISTS detection_feedback (
  id SERIAL PRIMARY KEY,
  detection_id INT REFERENCES detections(id) ON DELETE CASCADE,
  feedback TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_detections_event_id ON detections(event_id);
CREATE INDEX IF NOT EXISTS idx_detections_created_at ON detections(created_at);
CREATE INDEX IF NOT EXISTS idx_detection_feedback_detection_id ON detection_feedback(detection_id);
