from sync_agent.supabase_client import SupabaseSyncClient

def clear_db():
    print("Clearing fee_transactions (which cascades to fee_allocations)...")
    try:
        client = SupabaseSyncClient()
        # Delete all transactions
        res = client.client.table('fee_transactions').delete().neq('guid', 'dummy-non-existent-guid').execute()
        print(f"Deleted {len(res.data)} transaction records.")
    except Exception as e:
        print(f"Error deleting transactions: {e}")

if __name__ == "__main__":
    clear_db()
