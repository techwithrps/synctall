-- View to display detailed student-wise ledger vouchers with a running balance
DROP VIEW IF EXISTS public.student_ledger_vouchers;

CREATE OR REPLACE VIEW public.student_ledger_vouchers AS
SELECT 
    ft.guid AS entry_id,
    ft.enrollment_no,
    s.student_name,
    ft.date,
    -- Get the particulars: 
    -- 1. Try to get fee head from allocations
    -- 2. Try to get the parsed particulars column from Tally sync
    -- 3. Fallback to voucher type
    COALESCE(
        (SELECT fee_head FROM public.fee_allocations WHERE transaction_guid = ft.guid ORDER BY amount ASC LIMIT 1), 
        ft.particulars,
        ft.voucher_type
    ) AS particulars,
    ft.voucher_type,
    ft.voucher_number,
    -- Debit: represents fee charge (Due Fee). We use ABS to show positive ledger values.
    CASE 
        WHEN ft.voucher_type = 'Due Fee' THEN ABS(ft.amount)
        ELSE 0.00
    END AS debit,
    -- Credit: represents fee payment (Fees Receipt, Receipt, or Journal discount).
    CASE 
        WHEN ft.voucher_type IN ('Fees Receipt', 'Receipt', 'Journal') THEN ABS(ft.amount)
        ELSE 0.00
    END AS credit,
    -- Running Balance: Opening balance + Sum of (debits - credits) so far
    COALESCE(s.opening_balance, 0.00) + SUM(
        CASE 
            WHEN ft.voucher_type = 'Due Fee' THEN ABS(ft.amount)
            ELSE -ABS(ft.amount)
        END
    ) OVER (
        PARTITION BY ft.enrollment_no 
        -- Cast voucher_number to numeric to fix alphanumeric sorting (e.g. so 70 comes before 106)
        ORDER BY ft.date, NULLIF(regexp_replace(ft.voucher_number, '\D', '', 'g'), '')::numeric, ft.guid
    ) AS running_balance,
    ft.last_synced_at
FROM public.fee_transactions ft
LEFT JOIN public.students s ON ft.enrollment_no = s.enrollment_no
ORDER BY ft.enrollment_no, ft.date, NULLIF(regexp_replace(ft.voucher_number, '\D', '', 'g'), '')::numeric;


