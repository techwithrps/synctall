import oracledb
from sync_agent.config import settings

try:
    connection = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_CONNECT_STRING
    )
    cursor = connection.cursor()
    cursor.execute(f"SELECT COMPANY_ID, COUNT(*) FROM {settings.DB_SCHEMA}.STUDENT_MASTER_DATA GROUP BY COMPANY_ID")
    print("Student counts by COMPANY_ID:")
    for row in cursor.fetchall():
        print(f"Company ID: {row[0]}, Count: {row[1]}")
    cursor.close()
    connection.close()
except Exception as e:
    print("Database error:", e)
