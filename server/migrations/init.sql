-- Create ratings table
CREATE TABLE IF NOT EXISTS ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    accuracy INTEGER NOT NULL CHECK (accuracy >= 1 AND accuracy <= 5),
    efficiency INTEGER NOT NULL CHECK (efficiency >= 1 AND efficiency <= 5),
    usability INTEGER NOT NULL CHECK (usability >= 1 AND usability <= 5),
    stability INTEGER NOT NULL CHECK (stability >= 1 AND stability <= 5),
    overall DECIMAL(3,1) NOT NULL,
    comment VARCHAR(20),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ratings_tool_name ON ratings(tool_name);
CREATE INDEX IF NOT EXISTS idx_ratings_api_key ON ratings(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_ratings_timestamp ON ratings(timestamp);

-- Create tool_stats table
CREATE TABLE IF NOT EXISTS tool_stats (
    tool_name VARCHAR(255) PRIMARY KEY,
    total_ratings INTEGER NOT NULL DEFAULT 0,
    avg_accuracy DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_efficiency DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_usability DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_stability DECIMAL(3,1) NOT NULL DEFAULT 0,
    avg_overall DECIMAL(3,1) NOT NULL DEFAULT 0,
    last_updated TIMESTAMP
);

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create index for fast auth lookup
CREATE INDEX IF NOT EXISTS idx_agents_api_key_hash ON agents(api_key_hash);