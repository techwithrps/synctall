-- Create fee_transactions table
CREATE TABLE IF NOT EXISTS public.fee_transactions (
    guid TEXT PRIMARY KEY,
    date DATE,
    voucher_number TEXT,
    voucher_type TEXT,
    party_ledger_name TEXT,
    enrollment_no TEXT REFERENCES public.students(enrollment_no) ON DELETE SET NULL,
    amount NUMERIC(15, 2) DEFAULT 0.00,
    raw_payload JSONB DEFAULT '{}'::jsonb,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create index on enrollment_no for faster lookup
CREATE INDEX IF NOT EXISTS idx_fee_transactions_enrollment_no ON public.fee_transactions(enrollment_no);

-- Create fee_allocations table
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

-- Create index on transaction_guid
CREATE INDEX IF NOT EXISTS idx_fee_allocations_transaction_guid ON public.fee_allocations(transaction_guid);

-- Create transaction_sync_logs table
CREATE TABLE IF NOT EXISTS public.transaction_sync_logs (
    id BIGSERIAL PRIMARY KEY,
    job_id UUID REFERENCES public.sync_jobs(id) ON DELETE CASCADE,
    transaction_guid TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILED')),
    action TEXT DEFAULT 'UPSERT',
    error_message TEXT,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create index on job_id
CREATE INDEX IF NOT EXISTS idx_transaction_sync_logs_job_id ON public.transaction_sync_logs(job_id);
