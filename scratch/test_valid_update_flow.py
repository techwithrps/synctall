import sys
import os
import time

# Add root folder to sys.path so we can import sync_agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_agent.supabase_client import SupabaseSyncClient

def main():
    client = SupabaseSyncClient()
    tx_guid = "4415c7d4-c39d-48c8-9745-55d45216b25d"
    
    print("1. Updating allocations in Supabase to sum to 17,000.00...")
    res = client.client.table("fee_allocations").select("id, fee_head").eq("transaction_guid", tx_guid).execute()
    for alloc in res.data:
        if alloc['fee_head'] == "TUTION FEE":
            client.client.table("fee_allocations").update({"amount": 12000.00}).eq("id", alloc['id']).execute()
        elif alloc['fee_head'] == "REGISTRATION FEE":
            client.client.table("fee_allocations").update({"amount": 5000.00}).eq("id", alloc['id']).execute()
            
    print("Allocations updated in DB.")
    
    print("\n2. Updating transaction amount in Supabase to 17,000.00...")
    client.client.table("fee_transactions").update({
        "amount": 17000.00
    }).eq("guid", tx_guid).execute()
    
    print("Transaction amount updated in DB. Waiting 6 seconds for daemon to sync...")
    time.sleep(6.0)
    
    print("\nDone. Please check the daemon logs to verify sync success!")

if __name__ == "__main__":
    main()
