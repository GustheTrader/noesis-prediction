-- Sovereign OS — Database Initialization

-- Prediction Markets
CREATE TABLE IF NOT EXISTS markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'reality_os',
    status TEXT DEFAULT 'open',
    outcome BOOLEAN,
    yes_price FLOAT DEFAULT 0.5,
    no_price FLOAT DEFAULT 0.5,
    total_volume FLOAT DEFAULT 0,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    closes_at TIMESTAMP,
    resolved_at TIMESTAMP,
    tags TEXT[]
);

-- Predictions
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    member_id TEXT NOT NULL,
    prediction BOOLEAN NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    stake FLOAT DEFAULT 1.0,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Members
CREATE TABLE IF NOT EXISTS members (
    id TEXT PRIMARY KEY,
    name TEXT,
    joined_at TIMESTAMP DEFAULT NOW(),
    total_predictions INT DEFAULT 0,
    correct_predictions INT DEFAULT 0,
    reputation_score FLOAT DEFAULT 0.5,
    svrgn_balance FLOAT DEFAULT 0,
    svrgny_balance FLOAT DEFAULT 0
);

-- Agents
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT,
    skill_level FLOAT DEFAULT 0.5,
    strategy TEXT,
    budget FLOAT DEFAULT 100,
    status TEXT DEFAULT 'active',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transactions (SVRGN / SVRGN-Y)
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id TEXT REFERENCES members(id),
    type TEXT NOT NULL, -- 'earn', 'spend', 'transfer'
    amount FLOAT NOT NULL,
    token TEXT DEFAULT 'SVRGN', -- 'SVRGN' or 'SVRGN-Y'
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Leaderboard view
CREATE OR REPLACE VIEW leaderboard AS
SELECT
    m.id,
    m.name,
    m.total_predictions,
    m.correct_predictions,
    CASE WHEN m.total_predictions > 0
        THEN ROUND(m.correct_predictions::FLOAT / m.total_predictions::FLOAT, 4)
        ELSE 0
    END as accuracy,
    m.reputation_score,
    m.svrgn_balance
FROM members m
ORDER BY m.reputation_score DESC;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_predictions_market ON predictions(market_id);
CREATE INDEX IF NOT EXISTS idx_predictions_member ON predictions(member_id);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);
CREATE INDEX IF NOT EXISTS idx_markets_category ON markets(category);
CREATE INDEX IF NOT EXISTS idx_transactions_member ON transactions(member_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_agents_domain ON agents(domain);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- Insert default members
INSERT INTO members (id, name, reputation_score) VALUES
    ('jeff', 'Jeff Gus', 0.8),
    ('sunset', 'Sunset', 0.75),
    ('alice', 'Alice', 0.6),
    ('bob', 'Bob', 0.55),
    ('charlie', 'Charlie', 0.5)
ON CONFLICT (id) DO NOTHING;
