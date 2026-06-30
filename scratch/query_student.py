import oracledb
import sys

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"
enrollment_no = "GF/2021/8052"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    
    print(f"Searching Oracle DB for student: {enrollment_no}")
    cursor.execute("""
        SELECT * 
        FROM C##COLLAGETEST.STUDENT_MASTER_DATA 
        WHERE ENRL_NO = :enrl_no OR CRN = :enrl_no
    """, {"enrl_no": enrollment_no})
    
    row = cursor.fetchone()
    if row:
        col_names = [col[0] for col in cursor.description]
        print("-" * 50)
        for name, val in zip(col_names, row):
            if val is not None:
                print(f"{name}: {val}")
        print("-" * 50)
    else:
        print(f"No student record found with Enrollment No: {enrollment_no}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", str(e), file=sys.stderr)
    sys.exit(1)
