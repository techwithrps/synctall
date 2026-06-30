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
    
    # Update UPDATED_BY to 'INITIAL_IMPORT' for all Sri Sri University students
    cursor.execute("""
        UPDATE STUDENT_MASTER_DATA 
        SET UPDATED_BY = 'INITIAL_IMPORT' 
        WHERE COMPANY_ID = 11 AND TALLY_SYNC = 'S' AND UPDATED_BY = 'TALLY_SYNC'
    """)
    updated_rows = cursor.rowcount
    connection.commit()
    print(f"Successfully reset UPDATED_BY to 'INITIAL_IMPORT' for {updated_rows} Sri Sri students.")
    
    cursor.close()
    connection.close()
except Exception as e:
    print("Failed to run update:", e)
