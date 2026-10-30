-- Schema for Cloudflare D1 (Serverless SQL Database)
-- Stores multi-tenant accounts, connected platforms, and daily telemetry

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS platforms (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    platform_name TEXT NOT NULL, -- 'youtube', 'instagram', 'twitter', 'linkedin', 'devto', 'pinterest', 'threads'
    account_handle TEXT,
    access_token TEXT,
    refresh_token TEXT,
    is_connected INTEGER DEFAULT 1,
    last_sync TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS metrics_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    platform_name TEXT NOT NULL,
    followers_or_subs INTEGER DEFAULT 0,
    impressions_or_views INTEGER DEFAULT 0,
    engagements_or_likes INTEGER DEFAULT 0,
    recorded_date DATE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS scheduled_posts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    day_number INTEGER,
    title TEXT,
    topic TEXT,
    format TEXT, -- 'short_video', 'carousel', 'longform', 'tweet'
    status TEXT DEFAULT 'pending', -- 'pending', 'published', 'failed'
    published_url TEXT,
    scheduled_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
