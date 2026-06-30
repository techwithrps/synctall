import oracledb

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT BRANCH FROM C##COLLAGETEST.STUDENT_MASTER_DATA WHERE BRANCH IS NOT NULL")
    rows = cursor.fetchall()
    print("Distinct branches in Oracle DB:")
    for r in rows:
        print(f" - {r[0]}")
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
