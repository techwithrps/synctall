import oracledb

user = "C##ELOGIPAYCOLLEGE"
password = "ELOGIPAYCOLLEGE_1228#"
dsn = "103.234.185.186:1521/xe"
company_id = 12
schema = "C##ELOGIPAYCOLLEGE"

try:
    print(f"Connecting to Oracle DB ({schema}) to perform integration column and trigger setup...")
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    cursor = connection.cursor()
    
    # 1. Add TALLY_SYNC column to STUDENT_MASTER_DATA
    try:
        print("Checking if TALLY_SYNC column needs to be added...")
        # Check if column exists
        cursor.execute("SELECT column_name FROM user_tab_columns WHERE table_name = 'STUDENT_MASTER_DATA' AND column_name = 'TALLY_SYNC'")
        col_exists = cursor.fetchone()
        if not col_exists:
            print("Adding TALLY_SYNC column to STUDENT_MASTER_DATA table...")
            cursor.execute("ALTER TABLE STUDENT_MASTER_DATA ADD TALLY_SYNC VARCHAR2(10) DEFAULT NULL")
            print("Successfully added TALLY_SYNC column.")
        else:
            print("TALLY_SYNC column already exists.")
    except Exception as col_err:
        print("Error checking/adding column:", col_err)
        
    # 2. Create or Replace Trigger TRG_STUDENT_MARK_UNSYNCED
    trigger_sql = f"""
    CREATE OR REPLACE TRIGGER {schema}.TRG_STUDENT_MARK_UNSYNCED
    BEFORE UPDATE ON {schema}.STUDENT_MASTER_DATA
    FOR EACH ROW
    DECLARE
      v_fields_changed INTEGER := 0;
    BEGIN
      -- Check if any key data field has actually changed
      IF (
           NVL(TO_CHAR(:NEW.STUDENT_NAME),'~')      != NVL(TO_CHAR(:OLD.STUDENT_NAME),'~')
        OR NVL(TO_CHAR(:NEW.SESSION_YEAR),'~')      != NVL(TO_CHAR(:OLD.SESSION_YEAR),'~')
        OR NVL(TO_CHAR(:NEW.BRANCH),'~')            != NVL(TO_CHAR(:OLD.BRANCH),'~')
        OR NVL(TO_CHAR(:NEW.COURSE),'~')            != NVL(TO_CHAR(:OLD.COURSE),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_MOBILE),'~')    != NVL(TO_CHAR(:OLD.STUDENT_MOBILE),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_EMAIL_ID),'~')  != NVL(TO_CHAR(:OLD.STUDENT_EMAIL_ID),'~')
        OR NVL(TO_CHAR(:NEW.FATHER_NAME),'~')       != NVL(TO_CHAR(:OLD.FATHER_NAME),'~')
        OR NVL(TO_CHAR(:NEW.MOTHER_NAME),'~')       != NVL(TO_CHAR(:OLD.MOTHER_NAME),'~')
        OR NVL(TO_CHAR(:NEW.ROLL_NO),'~')           != NVL(TO_CHAR(:OLD.ROLL_NO),'~')
        OR NVL(TO_CHAR(:NEW.REG_NO),'~')            != NVL(TO_CHAR(:OLD.REG_NO),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_DOB),'~')       != NVL(TO_CHAR(:OLD.STUDENT_DOB),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_GENDER),'~')    != NVL(TO_CHAR(:OLD.STUDENT_GENDER),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_CATEGORY),'~')  != NVL(TO_CHAR(:OLD.STUDENT_CATEGORY),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_QUOTA),'~')     != NVL(TO_CHAR(:OLD.STUDENT_QUOTA),'~')
        OR NVL(TO_CHAR(:NEW.ACTIVE_STATUS_ID),'~')  != NVL(TO_CHAR(:OLD.ACTIVE_STATUS_ID),'~')
        OR NVL(TO_CHAR(:NEW.PERMANENT_ADDRESS),'~') != NVL(TO_CHAR(:OLD.PERMANENT_ADDRESS),'~')
        OR NVL(TO_CHAR(:NEW.CURRENT_ADDRESS),'~')   != NVL(TO_CHAR(:OLD.CURRENT_ADDRESS),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_RELIGION),'~')  != NVL(TO_CHAR(:OLD.STUDENT_RELIGION),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_CASTE),'~')     != NVL(TO_CHAR(:OLD.STUDENT_CASTE),'~')
        OR NVL(TO_CHAR(:NEW.STUDENT_STATUS),'~')    != NVL(TO_CHAR(:OLD.STUDENT_STATUS),'~')
      ) THEN
        v_fields_changed := 1;
      END IF;

      -- Only mark as U if:
      --   1. A real data field changed
      --   2. AND TALLY_SYNC is NOT being explicitly set to 'S' in this same statement
      IF v_fields_changed = 1 THEN
        IF NVL(:NEW.TALLY_SYNC, '~') = 'S' AND NVL(:OLD.TALLY_SYNC, '~') = 'S' THEN
          :NEW.TALLY_SYNC := 'U';
          :NEW.UPDATED_ON  := SYSDATE;
        ELSIF NVL(:NEW.TALLY_SYNC, '~') != 'S' THEN
          :NEW.TALLY_SYNC := 'U';
          :NEW.UPDATED_ON  := SYSDATE;
        END IF;
      END IF;
    END;
    """
    print("Creating/updating trigger C##ELOGIPAYCOLLEGE.TRG_STUDENT_MARK_UNSYNCED...")
    cursor.execute(trigger_sql)
    print("Successfully created/updated the trigger.")
    
    # 3. Update all students of company 12 to 'S'
    print(f"Setting TALLY_SYNC = 'S' for all students of Company ID {company_id}...")
    update_sql = """
        UPDATE STUDENT_MASTER_DATA
        SET TALLY_SYNC = 'S'
        WHERE COMPANY_ID = :company_id
    """
    cursor.execute(update_sql, {"company_id": company_id})
    row_count = cursor.rowcount
    connection.commit()
    
    print(f"SUCCESS: Marked {row_count} students of Company ID {company_id} as Synced (TALLY_SYNC = 'S').")
    
    cursor.close()
    connection.close()
except Exception as e:
    print("Execution failed:", e)
