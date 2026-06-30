import oracledb
from sync_agent.config import settings

try:
    connection = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_CONNECT_STRING
    )
    cursor = connection.cursor()
    cursor.execute(f"SELECT COMPANY_ID, COMPANY_CODE, COMPANY_NAME FROM {settings.DB_SCHEMA}.COMPANY_MASTER")
    print("DB Companies:")
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")
    cursor.close()
    connection.close()
except Exception as e:
    print("Database error:", e)
