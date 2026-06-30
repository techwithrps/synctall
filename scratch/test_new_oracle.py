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
    cursor.execute("SELECT COMPANY_ID, COMPANY_CODE, COMPANY_NAME FROM COMPANY_MASTER")
    print("Companies in new database:")
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")
    cursor.close()
    connection.close()
except Exception as e:
    print("Failed to query companies:", e)
