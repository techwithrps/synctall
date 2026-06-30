import oracledb

user = "C##ELOGIPAYCOLLEGE"
password = "ELOGIPAYCOLLEGE_1228#"
dsn = "103.234.185.186:1521/xe"
company_id = 12

try:
    print(f"Connecting to Oracle DB to identify and fix unsynced records for Company ID {company_id}...")
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    cursor = connection.cursor()
    
    # 1. Query the records that are not set to 'S'
    query = """
        SELECT ENRL_NO, STUDENT_NAME, STUDENT_STATUS, TALLY_SYNC, ACTIVE_STATUS_ID
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = :company_id
          AND (TALLY_SYNC IS NULL OR TALLY_SYNC != 'S')
    """
    cursor.execute(query, {"company_id": company_id})
    records = cursor.fetchall()
    
    print("\n--- FOUND UNSYNCED RECORDS ---")
    for r in records:
        print(f"Enrollment No: {r[0]} | Name: {r[1]} | Status: {r[2]} | TALLY_SYNC: {r[3]} | Active ID: {r[4]}")
        
    if not records:
        print("No unsynced records found.")
    else:
        # 2. Fix them by setting TALLY_SYNC = 'S'
        print(f"\nUpdating TALLY_SYNC to 'S' for all {len(records)} records...")
        update_query = """
            UPDATE STUDENT_MASTER_DATA
            SET TALLY_SYNC = 'S'
            WHERE COMPANY_ID = :company_id
              AND (TALLY_SYNC IS NULL OR TALLY_SYNC != 'S')
        """
        cursor.execute(update_query, {"company_id": company_id})
        connection.commit()
        print(f"SUCCESS: Marked {cursor.rowcount} records as Synced ('S').")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Database error:", e)
