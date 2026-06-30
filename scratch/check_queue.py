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
    
    # Query recent updates from STUDENT_MASTER_DATA_QUEUE for company 12
    query = """
        SELECT ENRL_NO, STUDENT_NAME, TRN_STATUS, TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI:SS'), UPDATED_BY
        FROM STUDENT_MASTER_DATA_QUEUE
        WHERE COMPANY_ID = 12
        ORDER BY UPDATED_ON DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print("Recent records in STUDENT_MASTER_DATA_QUEUE:")
    for idx, r in enumerate(rows[:20]):
        print(f"{idx+1}. Enroll: {r[0]} | Name: {r[1]} | TrnStatus: {r[2]} | UpdatedOn: {r[3]} | UpdatedBy: {r[4]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
