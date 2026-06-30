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
    
    # Let's inspect the 54 records created on 2026-06-24
    print("--- 54 NEWLY CREATED RECORDS ON 2026-06-24 ---")
    query_new = """
        SELECT ENRL_NO, STUDENT_NAME, TO_CHAR(CREATED_ON, 'YYYY-MM-DD HH24:MI:SS'), TALLY_SYNC, UPDATED_BY
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
          AND TRUNC(CREATED_ON) = TO_DATE('2026-06-24', 'YYYY-MM-DD')
    """
    cursor.execute(query_new)
    new_records = cursor.fetchall()
    for idx, r in enumerate(new_records):
        print(f"{idx+1}. Enroll: {r[0]} | Name: {r[1]} | Created: {r[2]} | TALLY_SYNC: {r[3]} | Updated By: {r[4]}")
        
    # Let's search for records updated on 2026-06-24 or 2026-06-23 where they are NOT in the 54 records
    # and might have been the 2 'U' records.
    print("\n--- POSSIBLY UPDATED RECORDS ON 2026-06-24 OR 2026-06-23 ---")
    query_updated = """
        SELECT ENRL_NO, STUDENT_NAME, TO_CHAR(CREATED_ON, 'YYYY-MM-DD HH24:MI:SS'), TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI:SS'), TALLY_SYNC, UPDATED_BY
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
          AND (TRUNC(UPDATED_ON) IN (TO_DATE('2026-06-24', 'YYYY-MM-DD'), TO_DATE('2026-06-23', 'YYYY-MM-DD'))
               OR TRUNC(DATA_UPDATED_DATE) IN (TO_DATE('2026-06-24', 'YYYY-MM-DD'), TO_DATE('2026-06-23', 'YYYY-MM-DD')))
          AND TRUNC(CREATED_ON) != TO_DATE('2026-06-24', 'YYYY-MM-DD')
    """
    cursor.execute(query_updated)
    updated_records = cursor.fetchall()
    for idx, r in enumerate(updated_records):
        print(f"{idx+1}. Enroll: {r[0]} | Name: {r[1]} | Created: {r[2]} | Updated: {r[3]} | TALLY_SYNC: {r[4]} | Updated By: {r[5]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
