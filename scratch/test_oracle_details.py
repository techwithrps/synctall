import oracledb
import sys

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    
    print("Listing ALL user synonyms:")
    cursor.execute("SELECT synonym_name, table_owner, table_name FROM user_synonyms")
    for row in cursor.fetchall():
        print(f"Synonym: {row[0]} -> {row[1]}.{row[2]}")

    print("\nListing user views:")
    cursor.execute("SELECT view_name FROM user_views")
    for row in cursor.fetchall():
        print(f"View: {row[0]}")

    print("\nListing table privileges granted to user:")
    cursor.execute("SELECT owner, table_name, privilege FROM user_tab_privs")
    for row in cursor.fetchall():
        print(f"Privilege: {row[2]} on {row[0]}.{row[1]}")

    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", str(e), file=sys.stderr)
    sys.exit(1)
