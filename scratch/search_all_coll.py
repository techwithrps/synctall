import oracledb
import sys

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    
    # Check if we can see any tables under owner C##COLLAGETEST or C##COLLEGETEST
    print("Checking tables owned by C##COLLAGETEST:")
    cursor.execute("""
        SELECT table_name FROM all_tables WHERE owner = 'C##COLLAGETEST'
    """)
    for row in cursor.fetchall():
        print(f" - {row[0]}")
        
    print("\nChecking if we can run a query on one of C##COLLAGETEST's tables:")
    try:
        cursor.execute("SELECT COUNT(*) FROM C##COLLAGETEST.STUDENT_API_DATA")
        count = cursor.fetchone()[0]
        print(f"C##COLLAGETEST.STUDENT_API_DATA has {count} rows")
    except Exception as query_err:
        print("Query failed:", str(query_err))

    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", str(e), file=sys.stderr)
    sys.exit(1)
