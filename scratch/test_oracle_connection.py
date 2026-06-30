import oracledb
import sys

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"

print("Attempting to connect to Oracle DB...")
try:
    # Use thin mode
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    print("SUCCESS: Connection established to Oracle database!")
    cursor = connection.cursor()
    
    # Let's query version or simple dual
    cursor.execute("SELECT banner FROM v$version")
    row = cursor.fetchone()
    print("Database Version:", row[0] if row else "Unknown")
    
    # Let's list some tables
    cursor.execute("SELECT table_name FROM user_tables")
    tables = cursor.fetchall()
    print("Tables in user schema:")
    for t in tables:
        print(f" - {t[0]}")
        
    cursor.close()
    connection.close()
except Exception as e:
    print("ERROR failed to connect:", str(e), file=sys.stderr)
    sys.exit(1)
