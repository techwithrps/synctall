import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sync_agent.supabase_client import SupabaseSyncClient

def main():
    client = SupabaseSyncClient()
    
    # We will execute the SQL via a REST call or just print it for the user.
    # Since we can't execute raw SQL through the Supabase client easily, we will provide the script.
    
    sql = """
DROP VIEW IF EXISTS public.student_ledger_vouchers;

CREATE OR REPLACE VIEW public.student_ledger_vouchers AS
SELECT 
    ft.guid AS entry_id,
    ft.enrollment_no,
    s.student_name,
    ft.date,
    ft.voucher_type AS particulars,
    ft.voucher_type,
    ft.voucher_number,
    -- Debit: represents fee charge (Due Fee). We use ABS to show positive ledger values.
    CASE 
        WHEN ft.voucher_type = 'Due Fee' THEN ABS(ft.amount)
        ELSE 0.00
    END AS debit,
    -- Credit: represents fee payment (Fees Receipt).
    CASE 
        WHEN ft.voucher_type = 'Fees Receipt' THEN ABS(ft.amount)
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
        ORDER BY ft.date, NULLIF(regexp_replace(ft.voucher_number, '\D', '', 'g'), '')::numeric, ft.guid
    ) AS running_balance,
    ft.last_synced_at
FROM public.fee_transactions ft
LEFT JOIN public.students s ON ft.enrollment_no = s.enrollment_no
ORDER BY ft.enrollment_no, ft.date, NULLIF(regexp_replace(ft.voucher_number, '\D', '', 'g'), '')::numeric, ft.guid;
"""
    print(sql)

if __name__ == "__main__":
    main()
