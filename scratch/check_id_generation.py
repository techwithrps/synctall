import oracledb
import sys

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    
    print("Triggers on STUDENT_MASTER_DATA:")
    cursor.execute("""
        SELECT trigger_name, trigger_type, triggering_event 
        FROM all_triggers 
        WHERE table_owner = 'C##COLLAGETEST' AND table_name = 'STUDENT_MASTER_DATA'
    """)
    for row in cursor.fetchall():
        print(f"Trigger: {row[0]}, Type: {row[1]}, Event: {row[2]}")
        
    print("\nChecking if STUDENT_ID is identity:")
    cursor.execute("""
        SELECT column_name, identity_column 
        FROM all_tab_cols 
        WHERE owner = 'C##COLLAGETEST' AND table_name = 'STUDENT_MASTER_DATA' AND column_name = 'STUDENT_ID'
    """)
    for row in cursor.fetchall():
        print(f"Col: {row[0]}, Identity: {row[1]}")
        
    print("\nSequence checking:")
    cursor.execute("""
        SELECT sequence_name FROM all_sequences WHERE sequence_owner = 'C##COLLAGETEST' AND sequence_name LIKE '%STUDENT%'
    """)
    for row in cursor.fetchall():
        print(f"Sequence: {row[0]}")

    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", str(e), file=sys.stderr)
    sys.exit(1)
