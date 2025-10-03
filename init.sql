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
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    log_level VARCHAR(10) NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Create indexes for better query performance
CREATE INDEX idx_job_logs_job_id ON job_logs(job_id);
CREATE INDEX idx_job_logs_timestamp ON job_logs(timestamp);
CREATE INDEX idx_job_logs_log_level ON job_logs(log_level);

-- Add comment to document the log levels
COMMENT ON COLUMN job_logs.log_level IS 'Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL';

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