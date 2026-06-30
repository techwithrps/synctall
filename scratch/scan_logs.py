import re
import os

log_dir = "c:\\Users\\F-tech\\Desktop\\codify\\synctal\\logs"
log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if "log" in f]

enrollments = set()
patterns = [
    re.compile(r"Syncing student ([\w/.-]+) to Tally"),
    re.compile(r"TALLY_SYNC set to '\w' for enrollment:\s*([\w/.-]+)"),
    re.compile(r"Successfully synced student ([\w/.-]+) to Tally")
]

print("Scanning log files for enrollments...")
for log_file in log_files:
    if not os.path.isfile(log_file):
        continue
    print(f"Reading {os.path.basename(log_file)}...")
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                for pattern in patterns:
                    m = pattern.search(line)
                    if m:
                        enrollments.add(m.group(1))
    except Exception as e:
        print(f"Error reading {log_file}: {e}")

print(f"Found {len(enrollments)} unique enrollments in logs.")
# Let's print a few of them
print("Sample enrollments from logs:", list(enrollments)[:20])

# Now let's connect to Oracle and check which of these enrollments are in Company ID 12
import oracledb
user = "C##ELOGIPAYCOLLEGE"
password = "ELOGIPAYCOLLEGE_1228#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    
    # We will query details of all enrollments from logs that belong to company 12
    # Since there are many, we can do it in batches or a single query if we filter
    placeholders = ",".join([f":{i}" for i in range(len(enrollments))])
    # To avoid expression too long or too many parameters (limit is 1000 in IN clause)
    enroll_list = list(enrollments)
    company_12_enrollments = []
    
    for i in range(0, len(enroll_list), 500):
        batch = enroll_list[i:i+500]
        params = {f"e{idx}": val for idx, val in enumerate(batch)}
        in_clause = ",".join([f":e{idx}" for idx in range(len(batch))])
        
        query = f"""
            SELECT ENRL_NO, TALLY_SYNC, UPDATED_BY, UPDATED_ON
            FROM STUDENT_MASTER_DATA
            WHERE COMPANY_ID = 12
              AND ENRL_NO IN ({in_clause})
        """
        cursor.execute(query, params)
        for row in cursor.fetchall():
            company_12_enrollments.append(row)
            
    print(f"Found {len(company_12_enrollments)} enrollments in database under Company ID 12.")
    
    # Let's print the status of these enrollments in the database
    by_status = {}
    for r in company_12_enrollments:
        status = r[1]
        by_status[status] = by_status.get(status, 0) + 1
    print("Database TALLY_SYNC distribution for logs enrollments:", by_status)
    
    cursor.close()
    connection.close()
except Exception as e:
    print("Oracle verification error:", e)
