import oracledb

user = "C##ELOGIPAYCOLLEGE"
password = "ELOGIPAYCOLLEGE_1228#"
dsn = "103.234.185.186:1521/xe"
company_id = 12

try:
    print(f"Connecting to Oracle DB to update TALLY_SYNC status for Company ID {company_id}...")
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    cursor = connection.cursor()
    
    # Run update query to set TALLY_SYNC = 'S' for COMPANY_ID = 12
    update_query = """
        UPDATE STUDENT_MASTER_DATA
        SET TALLY_SYNC = 'S'
        WHERE COMPANY_ID = :company_id
    """
    cursor.execute(update_query, {"company_id": company_id})
    row_count = cursor.rowcount
    
    connection.commit()
    print(f"SUCCESS: Updated {row_count} rows to TALLY_SYNC = 'S' for Company ID {company_id}.")
    
    cursor.close()
    connection.close()
except Exception as e:
    print("Database error:", e)
