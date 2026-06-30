import sys
import os
import time

# Add root folder to sys.path so we can import sync_agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sync_agent.supabase_client import SupabaseSyncClient

def main():
    client = SupabaseSyncClient()
    tx_guid = "4415c7d4-c39d-48c8-9745-55d45216b25d"
    
    # We do a dummy update: we set the amount to 19000.01 and then 19000.00, or we just set a last_synced_at timestamp to trigger the update event
    print("Performing dummy update on transaction to trigger realtime event...")
    res = client.client.table("fee_transactions").update({
        "amount": 19000.00,
        "party_ledger_name": "Test Kid 9396 -TST-9396"  # just touching it
    }).eq("guid", tx_guid).execute()
    
    print("Dummy update finished. Waiting 5 seconds for daemon...")
    time.sleep(5.0)
    
    print("\nDone. Please check the daemon log now!")

if __name__ == "__main__":
    main()
