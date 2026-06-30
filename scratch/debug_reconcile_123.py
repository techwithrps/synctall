import sys
sys.path.append("/Users/twrps/Desktop/synctal")

from sync_agent.tally_client import TallyClient
from sync_agent.supabase_client import SupabaseSyncClient as SupabaseClient

print("Initializing clients...")
tally = TallyClient()
sb = SupabaseClient()

print("Fetching student from Supabase...")
res = sb.client.table("students").select("*").execute()
db_students = res.data or []
db_map = {str(row["enrollment_no"]).strip(): row for row in db_students if row.get("enrollment_no")}

# Find students with is_left=True
left_students = [r for r in db_students if r.get("is_left")]
print(f"Total students marked is_left=True in DB: {len(left_students)}")
for s in left_students:
    print(f"  Enrollment: {s['enrollment_no']} | Name: {s['student_name']} | is_left: {s['is_left']}")

print("\nFetching ledger parents from Tally...")
tally_ledger_parents = tally.fetch_all_ledgers_with_parent()
print(f"Total ledger parents: {len(tally_ledger_parents)}")

# Inspect the target student (let's check "123" and any is_left=True student)
target_enrols = ["123", "1464646"]
for target_en in target_enrols:
    print(f"\n--- Debugging student {target_en} ---")
    db_rec = db_map.get(target_en)
    if not db_rec:
        print(f"Student {target_en} NOT found in Supabase DB!")
        continue
    
    clean_en_lower = target_en.lower()
    student_name = db_rec.get("student_name") or ""
    expected_ledger_name = f"{student_name.strip()} -{db_rec['enrollment_no']}".lower() if student_name else clean_en_lower
    
    parent_group = tally_ledger_parents.get(clean_en_lower) or tally_ledger_parents.get(expected_ledger_name)
    print(f"DB Rec: is_left={db_rec.get('is_left')} | student_name={student_name}")
    print(f"Expected Ledger Name: {expected_ledger_name}")
    print(f"Parent Group in Tally: {parent_group}")
    
    in_tally = parent_group is not None
    mismatched_parent = False
    is_left_db_bool = db_rec.get("is_left") in (True, "true", "True", "yes", "Yes", 1, "1")
    if in_tally:
        if is_left_db_bool and parent_group != "Left 2026":
            mismatched_parent = True
        elif not is_left_db_bool and parent_group == "Left 2026":
            mismatched_parent = True
            
    print(f"in_tally: {in_tally} | mismatched_parent: {mismatched_parent}")
