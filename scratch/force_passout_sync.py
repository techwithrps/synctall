from sync_agent.oracle_client import settings
import oracledb

conn = oracledb.connect(
    user=settings.DB_USER, 
    password=settings.DB_PASSWORD, 
    dsn=settings.DB_CONNECT_STRING
)
cur = conn.cursor()

# Count passed out students
cur.execute("SELECT COUNT(1) FROM C##COLLAGETEST.STUDENT_MASTER_DATA WHERE COMPANY_ID = 10 AND STUDENT_STATUS = 'P' AND (TALLY_SYNC != 'U' OR TALLY_SYNC IS NULL)")
count_p = cur.fetchone()[0]
print(f"Total remaining passed out students in DB to queue: {count_p}")

if count_p > 0:
    print(f"Forcing ALL {count_p} passed out students to sync queue by setting TALLY_SYNC = 'U'...")
    cur.execute("""
        UPDATE C##COLLAGETEST.STUDENT_MASTER_DATA 
        SET TALLY_SYNC = 'U' 
        WHERE COMPANY_ID = 10 AND STUDENT_STATUS = 'P' AND (TALLY_SYNC != 'U' OR TALLY_SYNC IS NULL)
    """)
    conn.commit()
    print("Done. They will be picked up by the sync agent in batches over the next few minutes.")
