import sys
sys.path.append("/Users/twrps/Desktop/synctal")

from sync_agent.tally_client import TallyClient
from sync_agent.parser import parse_students_xml
from sync_agent.supabase_client import SupabaseSyncClient
from sync_agent.sync_service import SyncService

service = SyncService()
tally = TallyClient()
db_client = SupabaseSyncClient()

print("Fetching from Tally...")
xml_data = tally.fetch_student_details()
tally_students = parse_students_xml(xml_data)

print("Fetching from Supabase...")
res = db_client.client.table("students").select("*").execute()
db_students = res.data
db_map = {str(row["enrollment_no"]).strip(): row for row in db_students if row.get("enrollment_no")}

differing_count = 0
for s in tally_students:
    en = s.get("enrollment_no")
    if not en:
        continue
    clean_en = str(en).strip()
    if clean_en in db_map:
        db_rec = db_map[clean_en]
        diff_fields = []
        fields_to_compare = [
            "student_name", "student_class", "roll_no", "registration_no", "course",
            "semester", "session", "year", "father_name", "mother_name", "quota",
            "gender", "dob", "blood_group", "mobile", "category", "subcategory",
            "email", "billwise", "admission_category", "seer_no", "rank", "religion",
            "caste", "annual_income", "status", "substatus", "opening_balance",
            "closing_balance", "permanent_address", "permanent_pin", "correspondence_address",
            "correspondence_pin", "created_by", "created_time", "remarks", "admission_mode"
        ]
        for field in fields_to_compare:
            val1 = s.get(field)
            val2 = db_rec.get(field)
            
            if field in ("opening_balance", "closing_balance", "annual_income"):
                if service._check_numeric_diff(val1, val2):
                    diff_fields.append((field, val1, val2))
            elif field == "billwise":
                if bool(val1) != bool(val2):
                    diff_fields.append((field, val1, val2))
            else:
                s1 = str(val1 or "").strip()
                s2 = str(val2 or "").strip()
                if s1 != s2:
                    diff_fields.append((field, val1, val2))
                    
        if diff_fields:
            differing_count += 1
            print(f"Student {clean_en} ({s.get('student_name')}) differs in fields:")
            for f, v1, v2 in diff_fields:
                print(f"  - {f}: Tally={repr(v1)}, DB={repr(v2)}")
            if differing_count >= 10:
                print("Too many differences, stopping print...")
                break

print(f"Total differing students: {differing_count}")
