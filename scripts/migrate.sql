-- migrate.sql
-- Create sequences
CREATE SEQUENCE IF NOT EXISTS user_id_seq;
CREATE SEQUENCE IF NOT EXISTS media_id_seq;
CREATE SEQUENCE IF NOT EXISTS playlist_id_seq;
CREATE SEQUENCE IF NOT EXISTS playlist_entry_id_seq;

-- Create tables
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY DEFAULT nextval('user_id_seq'),
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY DEFAULT nextval('media_id_seq'),
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    mime_type VARCHAR(100),
    size INTEGER,
    duration FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    title VARCHAR(255),
    description VARCHAR(1000),
    tags VARCHAR(500),
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY DEFAULT nextval('playlist_id_seq'),
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS playlist_entries (
    id INTEGER PRIMARY KEY DEFAULT nextval('playlist_entry_id_seq'),
    playlist_id INTEGER REFERENCES playlists(id) NOT NULL,
    media_id INTEGER REFERENCES media(id) NOT NULL,
    position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_media_user ON media(user_id);
CREATE INDEX IF NOT EXISTS idx_playlist_user ON playlists(user_id);
CREATE INDEX IF NOT EXISTS idx_playlist_entry_playlist ON playlist_entries(playlist_id);
CREATE INDEX IF NOT EXISTS idx_playlist_entry_position ON playlist_entries(position);

-- Create view for current playlist
CREATE OR REPLACE VIEW current_playlist AS
SELECT 
    m.filename,
    m.title,
    m.duration,
    pe.position
FROM playlist_entries pe
JOIN media m ON pe.media_id = m.id
JOIN playlists p ON pe.playlist_id = p.id
WHERE p.name = 'current'
ORDER BY pe.position;
