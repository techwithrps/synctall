import oracledb
from sync_agent.config import settings

try:
    connection = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_CONNECT_STRING
    )
    cursor = connection.cursor()
    
    # Query table structure
    cursor.execute(f"SELECT * FROM {settings.DB_SCHEMA}.COMPANY_MASTER")
    columns = [col[0] for col in cursor.description]
    print("Columns in COMPANY_MASTER:", columns)
    
    # Fetch all records
    print("\nRecords in COMPANY_MASTER:")
    for row in cursor.fetchall():
        record = dict(zip(columns, row))
        print(record)
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Database error:", e)
