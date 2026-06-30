import oracledb
import sys

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    
    print("Searching for tables containing 'STUDENT' or 'MASTER':")
    cursor.execute("""
        SELECT table_name, owner 
        FROM all_tables 
        WHERE (owner = :owner OR owner LIKE 'C##%')
          AND (table_name LIKE '%STUDENT%' OR table_name LIKE '%MASTER%' OR table_name LIKE '%FEE%')
    """, {"owner": user})
    rows = cursor.fetchall()
    for row in rows:
        print(f"Table: {row[0]}, Owner: {row[1]}")
        
    print("\nSearching for views containing 'STUDENT' or 'MASTER':")
    cursor.execute("""
        SELECT view_name, owner 
        FROM all_views 
        WHERE (owner = :owner OR owner LIKE 'C##%')
          AND (view_name LIKE '%STUDENT%' OR view_name LIKE '%MASTER%' OR view_name LIKE '%FEE%')
    """, {"owner": user})
    rows = cursor.fetchall()
    for row in rows:
        print(f"View: {row[0]}, Owner: {row[1]}")
        
    # Also print all tables just to see what exists under C##COLLEGETEST
    print("\nAll tables owned by C##COLLEGETEST:")
    cursor.execute("SELECT table_name FROM user_tables")
    for t in cursor.fetchall():
        print(f" - {t[0]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", str(e), file=sys.stderr)
    sys.exit(1)
