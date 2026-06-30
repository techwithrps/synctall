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
    cursor.execute("SELECT column_name, data_type FROM user_tab_columns WHERE table_name = 'STUDENT_MASTER_DATA'")
    print("Columns in STUDENT_MASTER_DATA:")
    for row in cursor.fetchall():
        print(f"- {row[0]} ({row[1]})")
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
