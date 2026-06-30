import sys
import os
import time

# Add root folder to sys.path so we can import sync_agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_agent.supabase_client import SupabaseSyncClient

def main():
    client = SupabaseSyncClient()
    tx_guid = "4415c7d4-c39d-48c8-9745-55d45216b25d"
    
    print("Fetching allocations for transaction...")
    res = client.client.table("fee_allocations").select("id, fee_head, amount").eq("transaction_guid", tx_guid).execute()
    if not res.data:
        print("No allocations found!")
        return
        
    print("Current Allocations in DB:")
    for alloc in res.data:
        print(f"  ID: {alloc['id']} | Fee Head: {alloc['fee_head']} | Amount: {alloc['amount']}")
        
    print("\nUpdating allocations to sum to 19,000.00 (Tution Fee: 13,000.00 | Registration Fee: 6,000.00)...")
    for alloc in res.data:
        if alloc['fee_head'] == "TUTION FEE":
            client.client.table("fee_allocations").update({"amount": 13000.00}).eq("id", alloc['id']).execute()
        elif alloc['fee_head'] == "REGISTRATION FEE":
            client.client.table("fee_allocations").update({"amount": 6000.00}).eq("id", alloc['id']).execute()
            
    print("Allocations updated. Waiting 5 seconds for daemon to capture the event and sync to Tally...")
    time.sleep(5.0)
    
    print("\nDone. Please inspect the daemon logs to see if it synced successfully!")

if __name__ == "__main__":
    main()
