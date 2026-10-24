-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    workspace_id INT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    page_count INT,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (workspace_id, sha256)
);

-- Chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    workspace_id INT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    document_id INT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    page_number INT,
    text TEXT NOT NULL,
    token_count INT NOT NULL,
    embedding vector(384) NOT NULL,
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);

-- Indexes for chunks
CREATE INDEX IF NOT EXISTS chunks_ws_idx ON chunks (workspace_id);
CREATE INDEX IF NOT EXISTS chunks_vec_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv);

-- Query logs table
CREATE TABLE IF NOT EXISTS query_logs (
    id BIGSERIAL PRIMARY KEY,
    workspace_id INT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    question_masked TEXT NOT NULL,
    route TEXT,
    answer TEXT,
    refused BOOLEAN NOT NULL DEFAULT FALSE,
    refusal_reason TEXT,
    chunk_ids BIGINT[] DEFAULT '{}',
    top_score REAL,
    tool_calls JSONB DEFAULT '[]',
    flags TEXT[] DEFAULT '{}',
    flagged BOOLEAN NOT NULL DEFAULT FALSE,
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS query_logs_ws_idx ON query_logs (workspace_id);
CREATE INDEX IF NOT EXISTS query_logs_flagged_idx ON query_logs (workspace_id, flagged);

-- Evaluation runs table
CREATE TABLE IF NOT EXISTS eval_runs (
    id SERIAL PRIMARY KEY,
    workspace_id INT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    summary JSONB,
    details JSONB
);

CREATE INDEX IF NOT EXISTS eval_runs_ws_idx ON eval_runs (workspace_id);
