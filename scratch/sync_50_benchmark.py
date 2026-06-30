import time
import oracledb
from sync_agent.oracle_client import OracleSyncClient
from sync_agent.tally_client import TallyClient

print("Initializing clients...")
oracle = OracleSyncClient()
tally = TallyClient()

# Fetch up to 50 unsynced students
connection = oracle._get_connection()
cursor = connection.cursor()
query = """
    SELECT ENRL_NO, STUDENT_NAME, BRANCH, ROLL_NO, REG_NO, COURSE, 
           SESSION_YEAR, FATHER_NAME, MOTHER_NAME, STUDENT_GENDER, 
           STUDENT_MOBILE, STUDENT_EMAIL_ID, CURRENT_ADDRESS, ACTIVE_STATUS_ID
    FROM C##COLLAGETEST.STUDENT_MASTER_DATA
    WHERE ENRL_NO IS NOT NULL AND TRN_STATUS = 'U' AND ROWNUM <= 50
"""
cursor.execute(query)
col_names = [col[0].lower() for col in cursor.description]
students = []
for row in cursor.fetchall():
    student_row = dict(zip(col_names, row))
    mapped_row = {
        "enrollment_no": student_row.get("enrl_no"),
        "student_name": student_row.get("student_name"),
        "student_class": student_row.get("branch"),
        "roll_no": student_row.get("roll_no"),
        "registration_no": student_row.get("reg_no"),
        "course": student_row.get("course"),
        "session": student_row.get("session_year"),
        "father_name": student_row.get("father_name"),
        "mother_name": student_row.get("mother_name"),
        "gender": student_row.get("student_gender"),
        "mobile": student_row.get("student_mobile"),
        "email": student_row.get("student_email_id"),
        "correspondence_address": student_row.get("current_address"),
        "permanent_address": student_row.get("current_address"),
        "is_left": student_row.get("active_status_id") == 0
    }
    students.append(mapped_row)

cursor.close()
connection.close()

if not students:
    print("No unsynced students (TRN_STATUS = 'U') left in DB. Benchmark completed beforehand!")
    exit(0)

print(f"Found {len(students)} unsynced students to benchmark sync speed.")
print("Starting benchmark...")
start_time = time.time()

synced_count = 0
for idx, s in enumerate(students):
    enrl_no = s.get("enrollment_no")
    print(f"[{idx+1}/{len(students)}] Syncing {enrl_no} ({s.get('student_name')})...")
    row_start = time.time()
    
    success = tally.sync_student_to_tally(enrl_no, s)
    
    if success:
        # Mark as synced in DB
        oracle.update_student_trn_status(enrl_no, 'S')
        synced_count += 1
        print(f" -> Success ({time.time() - row_start:.2f}s)")
    else:
        print(f" -> Failed ({time.time() - row_start:.2f}s)")

total_duration = time.time() - start_time
print("\n==================================================")
print("BENCHMARK COMPLETED")
print("==================================================")
print(f"Total synced: {synced_count}/{len(students)}")
print(f"Total Duration: {total_duration:.2f} seconds")
print(f"Average time per entry: {total_duration / len(students):.3f} seconds")
print("==================================================")
