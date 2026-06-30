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
    
    # Query triggers on STUDENT_MASTER_DATA
    query = """
        SELECT TRIGGER_NAME, TRIGGER_TYPE, TRIGGERING_EVENT, STATUS
        FROM USER_TRIGGERS
        WHERE TABLE_NAME = 'STUDENT_MASTER_DATA'
    """
    cursor.execute(query)
    print("Triggers:")
    for r in cursor.fetchall():
        print(f"Name: {r[0]} | Type: {r[1]} | Event: {r[2]} | Status: {r[3]}")
        
    # Get trigger text for any triggers
    cursor.execute(query)
    triggers = [row[0] for row in cursor.fetchall()]
    for trigger in triggers:
        print(f"\n--- TRIGGER TEXT FOR {trigger} ---")
        cursor.execute(f"SELECT TRIGGER_BODY FROM USER_TRIGGERS WHERE TRIGGER_NAME = '{trigger}'")
        row = cursor.fetchone()
        if row:
            print(row[0])
            
    cursor.close()
    connection.close()
except Exception as e:
    print("Error:", e)
