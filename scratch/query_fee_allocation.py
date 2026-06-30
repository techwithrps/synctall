import sys
import json
sys.path.append("/Users/twrps/Desktop/synctal")
from sync_agent.supabase_client import SupabaseSyncClient

def verify_allocations():
    client = SupabaseSyncClient()
    print("Fetching the latest fee transaction along with its allocations and student info...")
    
    # In Supabase, we can use the foreign key relationships to fetch joined data
    # We fetch a transaction, its allocations, and the student it belongs to.
    res = client.client.table("fee_transactions").select(
        "guid, enrollment_no, party_ledger_name, amount, "
        "fee_allocations(bill_name, fee_head, semester, amount), "
        "students(student_name, student_class)"
    ).limit(1).execute()
    
    if res.data and len(res.data) > 0:
        tx = res.data[0]
        print("\n--- TRANSACTION RECORD ---")
        print(f"Transaction GUID: {tx.get('guid')}")
        print(f"Party Ledger: {tx.get('party_ledger_name')}")
        print(f"Total Amount: {tx.get('amount')}")
        
        print("\n--- STUDENT MAPPING (Using enrollment_no) ---")
        print(f"Enrollment No: {tx.get('enrollment_no')}")
        student = tx.get('students')
        if student:
            print(f"Student Name: {student.get('student_name')}")
            print(f"Class: {student.get('student_class')}")
        else:
            print("Student: Not Found in students table (Might not be synced yet)")
            
        print("\n--- FEE ALLOCATIONS MAPPED TO THIS TRANSACTION ---")
        allocations = tx.get('fee_allocations', [])
        for i, alloc in enumerate(allocations, 1):
            print(f"  Allocation {i}:")
            print(f"    Fee Head: {alloc.get('fee_head')}")
            print(f"    Semester: {alloc.get('semester')}")
            print(f"    Bill Name: {alloc.get('bill_name')}")
            print(f"    Amount: {alloc.get('amount')}")
    else:
        print("No transactions found in the database.")

if __name__ == "__main__":
    verify_allocations()
