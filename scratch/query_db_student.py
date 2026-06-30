import sys
sys.path.append("/Users/twrps/Desktop/synctal")
from sync_agent.supabase_client import SupabaseSyncClient
from sync_agent.config import settings

client = SupabaseSyncClient()
enrollment_no = "1223"
print(f"Querying database for enrollment {enrollment_no}...")
res = client.client.table("students").select("*").eq("enrollment_no", enrollment_no).execute()
if res.data and len(res.data) > 0:
    print("\n--- STUDENT RECORD IN DB ---")
    for k, v in res.data[0].items():
        print(f"{k}: {v}")
else:
    print("Student not found in DB!")
