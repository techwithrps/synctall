from sync_agent.oracle_client import settings
import oracledb

conn = oracledb.connect(
    user=settings.DB_USER, 
    password=settings.DB_PASSWORD, 
    dsn=settings.DB_CONNECT_STRING
)
cur = conn.cursor()

# Get recent new students
cur.execute("""
    SELECT ENRL_NO, CREATED_ON 
    FROM C##COLLAGETEST.STUDENT_MASTER_DATA 
    WHERE COMPANY_ID = 10 AND TALLY_SYNC IS NULL 
    ORDER BY CREATED_ON DESC NULLS LAST
    FETCH FIRST 5 ROWS ONLY
""")
print("Most recently created NULL records:")
for row in cur.fetchall():
    print(f"{row[0]} - {row[1]}")
