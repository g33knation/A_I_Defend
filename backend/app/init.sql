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
  created_at TIMESTAMP DEFAULT now(),
  UNIQUE(detection_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_detections_event_id ON detections(event_id);
CREATE INDEX IF NOT EXISTS idx_detections_created_at ON detections(created_at);
CREATE INDEX IF NOT EXISTS idx_detection_feedback_detection_id ON detection_feedback(detection_id);

-- Defense actions taken by the system (autonomous defense)
CREATE TABLE IF NOT EXISTS defense_actions (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,      -- block_ip, unblock_ip, quarantine_file, restore_file, kill_process, alert
    target VARCHAR(500) NOT NULL,           -- IP address, file path, or PID
    reason TEXT,                            -- Why this action was taken
    trigger_event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
    trigger_detection_id INTEGER REFERENCES detections(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'active',    -- active, rolled_back, expired
    executed_by VARCHAR(100),               -- agent_id or 'ai' or 'manual'
    metadata JSONB,                         -- Additional action-specific data
    created_at TIMESTAMP DEFAULT NOW(),
    rolled_back_at TIMESTAMP
);

-- Defense configuration (thresholds, enabled features)
CREATE TABLE IF NOT EXISTS defense_config (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default defense configuration
INSERT INTO defense_config (key, value, description) VALUES
    ('autonomous_defense_enabled', 'true', 'Master switch for autonomous defense actions'),
    ('severity_threshold', '0.9', 'Minimum severity score to trigger autonomous defense (0.0-1.0)'),
    ('enabled_actions', '["block_ip", "quarantine_file", "alert"]', 'List of enabled defense action types'),
    ('blocked_ips_ttl_hours', '24', 'Hours before blocked IPs are automatically unblocked'),
    ('quarantine_path', '/quarantine', 'Directory for quarantined files')
ON CONFLICT (key) DO NOTHING;

-- Create indexes for defense tables
CREATE INDEX IF NOT EXISTS idx_defense_actions_status ON defense_actions(status);
CREATE INDEX IF NOT EXISTS idx_defense_actions_action_type ON defense_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_defense_actions_created_at ON defense_actions(created_at);

-- Centralized logging for agents
CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for querying logs by agent and time
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_time ON agent_logs(agent_id, created_at DESC);
