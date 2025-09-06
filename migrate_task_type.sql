-- Migration script to make task_type column non-nullable with default value
-- This migration ensures all existing jobs have a task_type and sets a default for new jobs

-- Step 1: Update any existing NULL task_type values to 'http_call' (the default)
UPDATE jobs 
SET task_type = 'http_call' 
WHERE task_type IS NULL;

-- Step 2: Make the task_type column non-nullable with default value
ALTER TABLE jobs 
ALTER COLUMN task_type SET NOT NULL,
ALTER COLUMN task_type SET DEFAULT 'http_call';

-- Step 3: Add a check constraint to ensure valid task types
ALTER TABLE jobs 
ADD CONSTRAINT valid_task_type 
CHECK (task_type IN ('http_call', 'data_transform', 'email_send', 'webhook_call', 'file_upload', 'report_generate'));

-- Step 4: Create an index on task_type for better query performance
CREATE INDEX IF NOT EXISTS idx_jobs_task_type ON jobs(task_type);

-- Step 5: Add a comment to document the task types
COMMENT ON COLUMN jobs.task_type IS 'Type of job task: http_call (default), data_transform, email_send, webhook_call, file_upload, report_generate';
