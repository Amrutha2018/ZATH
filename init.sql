-- jobs table
CREATE TABLE jobs (
id UUID PRIMARY KEY,
task_type VARCHAR(50),
payload JSONB,
callback_url TEXT,
status VARCHAR(20) NOT NULL DEFAULT 'queued',
retry_count INT NOT NULL DEFAULT 0,
callback_retry_count INT NOT NULL DEFAULT 0,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- job_logs table
CREATE TABLE job_logs (
id SERIAL PRIMARY KEY,
job_id UUID REFERENCES jobs(id),
log TEXT,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- users table
CREATE TABLE users (
id UUID PRIMARY KEY,
email VARCHAR(255) UNIQUE NOT NULL,
api_key VARCHAR(255) UNIQUE NOT NULL,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);