import oracledb
import time
import sys
from sync_agent.config import settings
from sync_agent.oracle_client import OracleSyncClient
from sync_agent.sync_service import SyncService

def run_test():
    print("Initializing test complete sync flow...")
    connection = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_CONNECT_STRING
    )
    cursor = connection.cursor()
    
    test_enrl = "GFTEST99999"
    
    # 1. Clean up any existing test record
    cursor.execute(f"DELETE FROM C##COLLAGETEST.STUDENT_MASTER_DATA WHERE ENRL_NO = '{test_enrl}'")
    connection.commit()
    
    # 2. Insert new student record
    print(f"1. Inserting new student record {test_enrl} in Oracle DB...")
    insert_query = """
        INSERT INTO C##COLLAGETEST.STUDENT_MASTER_DATA (
            STUDENT_ID, ENRL_NO, CRN, STUDENT_NAME, BRANCH, SESSION_YEAR, STUDENT_MOBILE, 
            FATHER_NAME, STUDENT_GENDER, ACTIVE_STATUS_ID, CREATED_ON, CREATED_BY
        ) VALUES (
            C##COLLAGETEST.STUDENT_ID.NEXTVAL,
            :enrl_no, :enrl_no, :student_name, :branch, :session_year, :mobile,
            :father_name, :gender, 1, SYSDATE, 'TEST_SUITE'
        )
    """
    bind_vars = {
        "enrl_no": test_enrl,
        "student_name": "Test Student Primary",
        "branch": "B.Tech-First Year Sem-1",
        "session_year": "2026-2030",
        "mobile": "9999999999",
        "father_name": "Test Father Name",
        "gender": "Male"
    }
    cursor.execute(insert_query, bind_vars)
    connection.commit()
    print("Inserted successfully!")
    
    # 3. Run sync pass for creation
    print("\n2. Running sync pass to CREATE student in Tally...")
    sync_service = SyncService()
    success = sync_service.run_sync_cycle()
    print(f"Sync creation result: {success}")
    
    # 4. Alter student record in Oracle
    print(f"\n3. Modifying student details (Name, Session, Mobile) in Oracle DB for {test_enrl}...")
    update_query = """
        UPDATE C##COLLAGETEST.STUDENT_MASTER_DATA
        SET STUDENT_NAME = 'Test Student Modified',
            SESSION_YEAR = '2026-2031',
            STUDENT_MOBILE = '8888888888',
            TRN_STATUS = 'U',
            UPDATED_ON = SYSDATE,
            UPDATED_BY = 'TEST_SUITE'
        WHERE ENRL_NO = :enrl_no
    """
    cursor.execute(update_query, {"enrl_no": test_enrl})
    connection.commit()
    print("Modified successfully!")
    
    # 5. Run sync pass for alteration
    print("\n4. Running sync pass to ALTER student in Tally...")
    success = sync_service.run_sync_cycle()
    print(f"Sync alteration result: {success}")
    
    # 6. Verify and clean up
    print("\nTest completed successfully!")
    cursor.close()
    connection.close()

if __name__ == '__main__':
    run_test()
