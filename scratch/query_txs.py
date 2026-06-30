import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sync_agent.supabase_client import SupabaseSyncClient

def main():
    client = SupabaseSyncClient()
    enrollment_no = "1223"
    
    print("--- STUDENT INFO ---")
    res_student = client.client.table("students").select("enrollment_no, student_name, opening_balance, closing_balance").eq("enrollment_no", enrollment_no).execute()
    for row in res_student.data:
        print(row)
        
    print("\n--- TRANSACTIONS (RAW) ---")
    res_tx = client.client.table("fee_transactions").select("guid, date, voucher_number, voucher_type, amount").eq("enrollment_no", enrollment_no).order("date").order("voucher_number").execute()
    for row in res_tx.data:
        print(f"guid: {row['guid']} | date: {row['date']} | vch_no: {row['voucher_number']} | type: {row['voucher_type']} | amount: {row['amount']}")

if __name__ == "__main__":
    main()
