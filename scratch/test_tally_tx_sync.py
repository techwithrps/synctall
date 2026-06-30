import sys
sys.path.append("/Users/twrps/Desktop/synctal")
from sync_agent.tally_client import TallyClient
from sync_agent.supabase_client import SupabaseSyncClient

def test_sync():
    client = SupabaseSyncClient()
    tally = TallyClient()
    
    # Fetch a real transaction from the DB
    print("Fetching one transaction from Supabase...")
    res = client.client.table("fee_transactions").select("*").limit(1).execute()
    if not res.data:
        print("No transactions found in DB.")
        return
        
    guid = res.data[0]["guid"]
    print(f"Testing two-way sync for transaction {guid}")
    
    full_tx = client.get_transaction_with_allocations(guid)
    if not full_tx:
        print("Failed to fetch full transaction details.")
        return
        
    print(f"Original Amount: {full_tx['amount']}")
    
    # Send it to tally
    print("Pushing transaction alteration to Tally...")
    success = tally.sync_transaction_to_tally(full_tx)
    
    if success:
        print("✅ SUCCESS! Tally accepted the Voucher Alteration XML payload!")
    else:
        print("❌ FAILED! Tally rejected the payload.")

if __name__ == "__main__":
    test_sync()
