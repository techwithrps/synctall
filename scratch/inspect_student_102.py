import sys
sys.path.append("/Users/twrps/Desktop/synctal")

from sync_agent.supabase_client import SupabaseSyncClient

client = SupabaseSyncClient()
res = client.client.table("students").select("*").eq("enrollment_no", "102").execute()

if res.data:
    print("Student 102 details in DB:")
    for k, v in res.data[0].items():
        print(f"  {k}: {repr(v)}")
else:
    print("Student 102 not found in DB.")
