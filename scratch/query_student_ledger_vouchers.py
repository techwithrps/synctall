import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_agent.supabase_client import SupabaseSyncClient

def main():
    print("Initializing Supabase Client...")
    client = SupabaseSyncClient()
    
    # Query student_ledger_vouchers view for TST-9396
    enrollment_no = "1223"
    print(f"Querying student_ledger_vouchers for enrollment {enrollment_no}... \n")
    try:
        res = client.client.table("student_ledger_vouchers").select("*").eq("enrollment_no", enrollment_no).execute()
        if res.data:
            print(f"Found {len(res.data)} records:")
            for i, row in enumerate(res.data, 1):
                print(f"\nRecord #{i}:")
                for k, v in row.items():
                    print(f"  {k}: {v}")
        else:
            print("No records found in student_ledger_vouchers for TST-9396.")
    except Exception as e:
        print(f"Error querying view: {e}")

if __name__ == "__main__":
    main()
