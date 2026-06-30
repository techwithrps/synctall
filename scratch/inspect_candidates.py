import oracledb

user = "C##ELOGIPAYCOLLEGE"
password = "ELOGIPAYCOLLEGE_1228#"
dsn = "103.234.185.186:1521/xe"

candidates = [
    "UGO202360925", "PGO24222266", "UGO26876830", "PGO26874089", 
    "UGO26882086", "UGO26878342", "PGO26868225", "PGO26878004", 
    "UGO26936245", "PGO26934987"
]

try:
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    cursor = connection.cursor()
    
    in_clause = ",".join([f"'{c}'" for c in candidates])
    query = f"""
        SELECT ENRL_NO, STUDENT_NAME, DATA_UPDATED, TO_CHAR(DATA_UPDATED_DATE, 'YYYY-MM-DD HH24:MI:SS'), 
               UPDATED_BY, TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI:SS'), TPT_STATUS, ACTIVE_STATUS_ID, STUDENT_STATUS
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
          AND ENRL_NO IN ({in_clause})
    """
    cursor.execute(query)
    for row in cursor.fetchall():
        print(f"Enroll: {row[0]} | Name: {row[1]} | DataUpdated: {row[2]} | DataUpdatedDate: {row[3]} | UpdatedBy: {row[4]} | UpdatedOn: {row[5]} | TptStatus: {row[6]} | ActiveID: {row[7]} | StudStatus: {row[8]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
