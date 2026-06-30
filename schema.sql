-- Tally EDU integration schema
-- Run this in Supabase SQL Editor to initialize all required tables.

-- Disable row-level security (RLS) or enable it according to project needs.
-- For simple setup, we keep it enabled but allow all service-role access.

-- 1. Sync Jobs Table (Orchestrator tracks)
CREATE TABLE IF NOT EXISTS public.sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    total INTEGER DEFAULT 0,
    processed INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 2. Students Master Table
CREATE TABLE IF NOT EXISTS public.students (
    enrollment_no TEXT PRIMARY KEY,
    student_name TEXT NOT NULL DEFAULT 'Unknown Student',
    student_class TEXT,
    roll_no TEXT,
    registration_no TEXT,
    course TEXT,
    semester TEXT,
    session TEXT,
    year TEXT,
    father_name TEXT,
    mother_name TEXT,
    quota TEXT,
    gender TEXT,
    dob DATE,
    blood_group TEXT,
    mobile TEXT,
    category TEXT,
    subcategory TEXT,
    email TEXT,
    billwise BOOLEAN DEFAULT FALSE,
    admission_category TEXT,
    seer_no TEXT,
    rank TEXT,
    religion TEXT,
    caste TEXT,
    annual_income NUMERIC(15, 2) DEFAULT 0.00,
    status TEXT,
    substatus TEXT,
    is_left BOOLEAN DEFAULT FALSE,
    date_of_leaving DATE,
    left_class TEXT,
    opening_balance NUMERIC(15, 2) DEFAULT 0.00,
    closing_balance NUMERIC(15, 2) DEFAULT 0.00,
    permanent_address TEXT,
    permanent_pin TEXT,
    correspondence_address TEXT,
    correspondence_pin TEXT,
    created_by TEXT,
    created_time TIMESTAMP WITH TIME ZONE,
    remarks TEXT,
    admission_mode TEXT,
    raw_payload JSONB DEFAULT '{}'::jsonb,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for student name search
CREATE INDEX IF NOT EXISTS idx_students_student_name ON public.students (student_name);
-- Index for student class filter
CREATE INDEX IF NOT EXISTS idx_students_student_class ON public.students (student_class);

-- 3. Individual Student Sync Logs (Traceability)
CREATE TABLE IF NOT EXISTS public.student_sync_logs (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID REFERENCES public.sync_jobs(id) ON DELETE CASCADE,
    enrollment_no TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
    action TEXT DEFAULT 'UPSERT',
    error_message TEXT,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index on job_id for faster dashboard trace retrievals
CREATE INDEX IF NOT EXISTS idx_student_sync_logs_job_id ON public.student_sync_logs (job_id);

-- 4. Fee Transactions
CREATE TABLE IF NOT EXISTS public.fee_transactions (
    guid TEXT PRIMARY KEY,
    date DATE,
    voucher_number TEXT,
    voucher_type TEXT,
    party_ledger_name TEXT,
    particulars TEXT,
    enrollment_no TEXT REFERENCES public.students(enrollment_no) ON DELETE SET NULL,
    amount NUMERIC(15, 2) DEFAULT 0.00,
    raw_payload JSONB DEFAULT '{}'::jsonb,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index on enrollment_no for faster lookup
CREATE INDEX IF NOT EXISTS idx_fee_transactions_enrollment_no ON public.fee_transactions(enrollment_no);

-- 5. Fee Allocations (Bill wise breakdown)
CREATE TABLE IF NOT EXISTS public.fee_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_guid TEXT NOT NULL REFERENCES public.fee_transactions(guid) ON DELETE CASCADE,
    bill_name TEXT NOT NULL,
    bill_type TEXT,
    amount NUMERIC(15, 2) DEFAULT 0.00,
    fee_head TEXT,
    semester TEXT,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE (transaction_guid, bill_name)
);

-- Index on transaction_guid
CREATE INDEX IF NOT EXISTS idx_fee_allocations_transaction_guid ON public.fee_allocations(transaction_guid);

-- 6. Transaction Sync Logs (Traceability)
CREATE TABLE IF NOT EXISTS public.transaction_sync_logs (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID REFERENCES public.sync_jobs(id) ON DELETE CASCADE,
    transaction_guid TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
    action TEXT DEFAULT 'UPSERT',
    error_message TEXT,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index on job_id for faster dashboard trace retrievals
CREATE INDEX IF NOT EXISTS idx_transaction_sync_logs_job_id ON public.transaction_sync_logs(job_id);

-- Enable Realtime for fee_transactions
ALTER PUBLICATION supabase_realtime ADD TABLE fee_transactions;
