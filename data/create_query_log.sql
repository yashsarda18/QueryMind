CREATE TABLE query_log (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    sql TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);