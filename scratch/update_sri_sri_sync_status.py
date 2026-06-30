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
    
    # Check count of students for Company ID 11
    cursor.execute("SELECT COUNT(1) FROM STUDENT_MASTER_DATA WHERE COMPANY_ID = 11")
    total_students = cursor.fetchone()[0]
    print(f"Total students for Sri Sri University (ID 11): {total_students}")
    
    # Check current TALLY_SYNC values distribution
    cursor.execute("""
        SELECT TALLY_SYNC, COUNT(1) 
        FROM STUDENT_MASTER_DATA 
        WHERE COMPANY_ID = 11 
        GROUP BY TALLY_SYNC
    """)
    print("Current TALLY_SYNC distribution:")
    for row in cursor.fetchall():
        print(f"Status: '{row[0]}', Count: {row[1]}")
        
    # Update to 'S'
    cursor.execute("""
        UPDATE STUDENT_MASTER_DATA 
        SET TALLY_SYNC = 'S', UPDATED_BY = 'TALLY_SYNC' 
        WHERE COMPANY_ID = 11
    """)
    updated_rows = cursor.rowcount
    connection.commit()
    print(f"Successfully marked {updated_rows} students as TALLY_SYNC = 'S'.")
    
    cursor.close()
    connection.close()
except Exception as e:
    print("Failed to run update:", e)
