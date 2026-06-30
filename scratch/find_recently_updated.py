import oracledb
from datetime import datetime

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
    
    # Query recently updated records for Shoolini (ID 12)
    # Let's count them by date or list those updated today
    query = """
        SELECT TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI'), COUNT(1)
        FROM STUDENT_MASTER_DATA
        WHERE COMPANY_ID = 12
        GROUP BY TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI')
        ORDER BY TO_CHAR(UPDATED_ON, 'YYYY-MM-DD HH24:MI') DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    print("Recently updated records count by minute:")
    for r in rows:
        print(f"Time: {r[0]} | Count: {r[1]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
