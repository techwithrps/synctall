import oracledb
import sys

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    
    print("Columns in C##COLLAGETEST.STUDENT_MASTER_DATA:")
    cursor.execute("""
        SELECT column_name, data_type, nullable 
        FROM all_tab_cols 
        WHERE owner = 'C##COLLAGETEST' AND table_name = 'STUDENT_MASTER_DATA'
        ORDER BY column_id
    """)
    for row in cursor.fetchall():
        print(f" - {row[0]}: {row[1]} (Nullable: {row[2]})")
        
    print("\nFirst 3 rows from C##COLLAGETEST.STUDENT_MASTER_DATA:")
    cursor.execute("""
        SELECT * FROM (
            SELECT * FROM C##COLLAGETEST.STUDENT_MASTER_DATA
        ) WHERE ROWNUM <= 3
    """)
    col_names = [col[0] for col in cursor.description]
    for row in cursor.fetchall():
        print("-" * 40)
        for name, val in zip(col_names, row):
            print(f"{name}: {val}")

    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", str(e), file=sys.stderr)
    sys.exit(1)
