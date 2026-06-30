import oracledb
from sync_agent.config import settings

def view_trigger():
    connection = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_CONNECT_STRING
    )
    cursor = connection.cursor()
    
    # Query to fetch the trigger definition and status
    query = """
        SELECT TRIGGER_NAME, STATUS, TRIGGER_TYPE, TRIGGERING_EVENT, TRIGGER_BODY
        FROM ALL_TRIGGERS
        WHERE TRIGGER_NAME = 'TRG_STUD_MASTER_UPD_TALLY'
    """
    cursor.execute(query)
    row = cursor.fetchone()
    if row:
        print(f"Trigger Name: {row[0]}")
        print(f"Status: {row[1]}")
        print(f"Type: {row[2]}")
        print(f"Event: {row[3]}")
        print("\nTrigger Body:")
        print(row[4])
    else:
        print("Trigger TRG_STUD_MASTER_UPD_TALLY not found.")
        
    cursor.close()
    connection.close()

if __name__ == '__main__':
    view_trigger()
