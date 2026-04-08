-- v0.0.3: Add key_prefix column for auth performance optimization

-- 1. Add key_prefix column
ALTER TABLE agents ADD COLUMN IF NOT EXISTS key_prefix VARCHAR(10) NOT NULL DEFAULT '';

-- 2. Create index on key_prefix
CREATE INDEX IF NOT EXISTS idx_agents_key_prefix ON agents(key_prefix);

-- 3. Truncate old agent records (cannot backfill key_prefix from bcrypt hashes)
TRUNCATE TABLE agents;
