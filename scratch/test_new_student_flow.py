import sys
import os
import time
import uuid
import random

# Add root folder to sys.path so we can import sync_agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_agent.supabase_client import SupabaseSyncClient

def main():
    print("Initializing Supabase Sync Client...")
    db_client = SupabaseSyncClient()
    
    # Generate unique suffix
    rand_id = str(random.randint(1000, 9999))
    enrollment_no = f"TST-{rand_id}"
    student_name = f"Test Kid {rand_id}"
    student_class = "BBA 1ST YEAR Sem-1"
    
    print(f"\n1. Creating a brand new student: {student_name} ({enrollment_no})")
    student_record = {
        "enrollment_no": enrollment_no,
        "student_name": student_name,
        "student_class": student_class,
        "billwise": True,
        "opening_balance": 0.0,
        "closing_balance": 0.0
    }
    
    res_student = db_client.client.table("students").insert(student_record).execute()
    print("Database Response for Student Insert:", res_student.data)
    
    print("\nSleeping for 5 seconds to let the daemon detect student insert and create the Tally ledger...")
    time.sleep(5.0)
    
    # Now create a Due Fee voucher for 15,000
    vch_guid = str(uuid.uuid4())
    vch_number = f"VCH-{rand_id}"
    voucher_type = "Due Fee"
    amount = 15000.00
    party_ledger_name = f"{student_name} -{enrollment_no}"
    
    print(f"\n2. Creating a brand new '{voucher_type}' transaction of {amount} for {enrollment_no}")
    transaction_record = {
        "guid": vch_guid,
        "date": "2025-04-01",  # Hardcoded 1st April
        "voucher_number": vch_number,
        "voucher_type": voucher_type,
        "party_ledger_name": party_ledger_name,
        "enrollment_no": enrollment_no,
        "amount": amount
    }
    
    res_tx = db_client.client.table("fee_transactions").insert(transaction_record).execute()
    print("Database Response for Transaction Insert:", res_tx.data)
    
    # Insert matching fee allocations (Tution Fee + Registration Fee)
    print("\n3. Inserting matching fee allocations...")
    allocation_records = [
        {
            "transaction_guid": vch_guid,
            "bill_name": f"2025-2026-Sem-1-TUTION FEE-{rand_id}",
            "bill_type": "New Ref",
            "amount": 10000.00,
            "fee_head": "TUTION FEE",
            "semester": "Sem-1"
        },
        {
            "transaction_guid": vch_guid,
            "bill_name": f"2025-2026-Sem-1-REGISTRATION FEE-{rand_id}",
            "bill_type": "New Ref",
            "amount": 5000.00,
            "fee_head": "REGISTRATION FEE",
            "semester": "Sem-1"
        }
    ]
    
    res_alloc = db_client.client.table("fee_allocations").insert(allocation_records).execute()
    print("Database Response for Allocations Insert:", res_alloc.data)
    
    print("\nTest records inserted. Daemon will wait 2.0s before performing transaction sync.")
    print("Sleeping for 8 seconds to allow daemon processing and completion...")
    time.sleep(8.0)
    
    print("\nCheck finished. You should inspect the background daemon logs to verify sync success!")

if __name__ == "__main__":
    main()
