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
    
    # Check current UPDATED_BY values distribution for Company ID 12 (Shoolini)
    cursor.execute("""
        SELECT UPDATED_BY, COUNT(1) 
        FROM STUDENT_MASTER_DATA 
        WHERE COMPANY_ID = 12 AND TALLY_SYNC = 'S'
        GROUP BY UPDATED_BY
    """)
    print("Shoolini (ID 12) UPDATED_BY distribution where TALLY_SYNC = 'S':")
    for row in cursor.fetchall():
        print(f"Updated By: '{row[0]}', Count: {row[1]}")
        
    # Check current UPDATED_BY values distribution for Company ID 11 (Sri Sri)
    cursor.execute("""
        SELECT UPDATED_BY, COUNT(1) 
        FROM STUDENT_MASTER_DATA 
        WHERE COMPANY_ID = 11 AND TALLY_SYNC = 'S'
        GROUP BY UPDATED_BY
    """)
    print("\nSri Sri (ID 11) UPDATED_BY distribution where TALLY_SYNC = 'S':")
    for row in cursor.fetchall():
        print(f"Updated By: '{row[0]}', Count: {row[1]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Failed to check distribution:", e)
