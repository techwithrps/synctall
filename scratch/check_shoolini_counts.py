import oracledb

user = "C##ELOGIPAYCOLLEGE"
password = "ELOGIPAYCOLLEGE_1228#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    cursor = connection.cursor()
    
    # Check count and TALLY_SYNC distribution for Shoolini (ID 12)
    cursor.execute("""
        SELECT TALLY_SYNC, STUDENT_STATUS, COUNT(1) 
        FROM STUDENT_MASTER_DATA 
        WHERE COMPANY_ID = 12 
        GROUP BY TALLY_SYNC, STUDENT_STATUS
    """)
    print("Shoolini (ID 12) distribution:")
    for row in cursor.fetchall():
        print(f"Sync Status: '{row[0]}', Student Status: '{row[1]}', Count: {row[2]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Failed to check distribution:", e)
