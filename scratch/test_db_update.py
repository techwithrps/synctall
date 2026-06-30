import asyncio
import sys
import logging
from sync_agent.supabase_client import SupabaseSyncClient

logging.basicConfig(level=logging.DEBUG)

async def main():
    client = SupabaseSyncClient()
    
    # 1. Update the allocation first (Tution Fee)
    print("Updating Tution Fee allocation to 35000...")
    res1 = client.client.table("fee_allocations").update({
        "amount": 35000
    }).eq("transaction_guid", "8c9a02d9-e165-4cfd-b7ba-85e43a211ad2-000000e9").eq("fee_head", "TUTION FEE").execute()
    print("Allocation Update Result:", res1.data)
    
    # 2. Update the transaction amount
    print("Updating Transaction amount to 55000...")
    res2 = client.client.table("fee_transactions").update({
        "amount": 55000
    }).eq("guid", "8c9a02d9-e165-4cfd-b7ba-85e43a211ad2-000000e9").execute()
    print("Transaction Update Result:", res2.data)

if __name__ == "__main__":
    asyncio.run(main())
