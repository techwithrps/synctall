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
    
    # Let's check the distribution of CREATED_ON dates
    query = """
        SELECT TO_CHAR(CREATED_ON, 'YYYY-MM-DD'), COUNT(1)
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
        GROUP BY TO_CHAR(CREATED_ON, 'YYYY-MM-DD')
        ORDER BY TO_CHAR(CREATED_ON, 'YYYY-MM-DD') DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print("CREATED_ON distribution for Shoolini (ID 12):")
    for r in rows[:30]:
        print(f"Date: {r[0]} | Count: {r[1]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
