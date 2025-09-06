-- jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL DEFAULT 'http_call',
    payload JSONB,
    callback_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    retry_count INT NOT NULL DEFAULT 0,
    callback_retry_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_task_type CHECK (task_type IN ('http_call', 'data_transform', 'email_send', 'webhook_call', 'file_upload', 'report_generate'))
);

-- Create index on task_type for better query performance
CREATE INDEX idx_jobs_task_type ON jobs(task_type);

-- Add comment to document the task types
COMMENT ON COLUMN jobs.task_type IS 'Type of job task: http_call (default), data_transform, email_send, webhook_call, file_upload, report_generate';
-- job_logs table
CREATE TABLE job_logs (
    id SERIAL PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    log TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Note: Dead letter queue is implemented using Redis, not a database table
-- This allows for better performance and easier integration with the job processing system

-- users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);