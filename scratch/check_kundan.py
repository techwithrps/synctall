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
    
    # Query records where UPDATED_BY = 'kundan_Online'
    query = """
        SELECT ENRL_NO, STUDENT_NAME, TALLY_SYNC, UPDATED_BY, TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI:SS')
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
          AND UPDATED_BY = 'kundan_Online'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print("kundan_Online records:")
    for r in rows:
        print(f"Enroll: {r[0]} | Name: {r[1]} | TALLY_SYNC: {r[2]} | UpdatedBy: {r[3]} | UpdatedOn: {r[4]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
