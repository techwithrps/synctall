import sys
import os

# Add root folder to sys.path so we can import sync_agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_agent.supabase_client import SupabaseSyncClient

def main():
    client = SupabaseSyncClient()
    tx_guid = "4415c7d4-c39d-48c8-9745-55d45216b25d"
    
    print(f"Querying transaction: {tx_guid}")
    res = client.client.table("fee_transactions").select(
        "guid, enrollment_no, party_ledger_name, amount, voucher_type, "
        "fee_allocations(bill_name, fee_head, semester, amount)"
    ).eq("guid", tx_guid).execute()
    
    if not res.data:
        print("Transaction not found!")
        return
        
    tx = res.data[0]
    print("\n--- TRANSACTION RECORD ---")
    print(f"Transaction GUID: {tx.get('guid')}")
    print(f"Voucher Type: {tx.get('voucher_type')}")
    print(f"Total Amount in fee_transactions: {tx.get('amount')}")
    
    print("\n--- FEE ALLOCATIONS ---")
    allocations = tx.get('fee_allocations', [])
    alloc_sum = 0.0
    for i, alloc in enumerate(allocations, 1):
        amt = float(alloc.get('amount', 0.0))
        alloc_sum += amt
        print(f"  {i}. Fee Head: {alloc.get('fee_head')} | Bill: {alloc.get('bill_name')} | Amount: {amt}")
        
    print(f"\nSum of fee allocations: {alloc_sum}")
    print(f"Difference (Transaction Amount - Allocations Sum): {float(tx.get('amount', 0.0)) - alloc_sum}")

if __name__ == "__main__":
    main()
