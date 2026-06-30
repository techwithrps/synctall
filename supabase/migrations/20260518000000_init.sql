-- Create students table
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_no VARCHAR(100) UNIQUE NOT NULL,
    student_name VARCHAR(255) NOT NULL,
    student_class VARCHAR(100),
    roll_no VARCHAR(50),
    registration_no VARCHAR(100),
    course VARCHAR(100),
    semester VARCHAR(50),
    session VARCHAR(50),
    year VARCHAR(50),
    father_name VARCHAR(255),
    mother_name VARCHAR(255),
    quota VARCHAR(100),
    gender VARCHAR(20),
    dob DATE,
    blood_group VARCHAR(10),
    mobile VARCHAR(50),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    email VARCHAR(255),
    billwise BOOLEAN DEFAULT FALSE,
    admission_category VARCHAR(100),
    seer_no VARCHAR(100),
    rank VARCHAR(50),
    religion VARCHAR(100),
    caste VARCHAR(100),
    annual_income NUMERIC(15, 2),
    status VARCHAR(50),
    substatus VARCHAR(50),
    opening_balance NUMERIC(15, 2),
    closing_balance NUMERIC(15, 2),
    permanent_address TEXT,
    permanent_pin VARCHAR(20),
    correspondence_address TEXT,
    correspondence_pin VARCHAR(20),
    created_by VARCHAR(100),
    created_time TIMESTAMP,
    remarks TEXT,
    admission_mode VARCHAR(100),
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create sync_jobs table for tracking sync execution
CREATE TABLE IF NOT EXISTS sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL, -- 'RUNNING', 'COMPLETED', 'FAILED'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create student_sync_logs table for audit/debugging
CREATE TABLE IF NOT EXISTS student_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_job_id UUID REFERENCES sync_jobs(id) ON DELETE CASCADE,
    enrollment_no VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'SUCCESS', 'FAILED'
    action_taken VARCHAR(50), -- 'INSERT', 'UPDATE', 'SKIP'
    error_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for optimization
CREATE INDEX IF NOT EXISTS idx_students_enrollment_no ON students(enrollment_no);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(student_name);
CREATE INDEX IF NOT EXISTS idx_students_course_sem ON students(course, semester);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON sync_jobs(status);
CREATE INDEX IF NOT EXISTS idx_student_sync_logs_job ON student_sync_logs(sync_job_id);

-- Trigger for auto-updating updated_at on students
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
