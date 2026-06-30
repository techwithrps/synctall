import oracledb
import sys
from sync_agent.config import settings

def main():
    try:
        connection = oracledb.connect(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            dsn=settings.DB_CONNECT_STRING
        )
        cursor = connection.cursor()
        
        sql = """
        CREATE OR REPLACE TRIGGER C##COLLAGETEST.TRG_STUDENT_MARK_UNSYNCED
        BEFORE UPDATE ON C##COLLAGETEST.STUDENT_MASTER_DATA
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
          --      (when our sync agent marks S, it does so in the same UPDATE — we allow that)
          IF v_fields_changed = 1 THEN
            IF NVL(:NEW.TALLY_SYNC, '~') = 'S' AND NVL(:OLD.TALLY_SYNC, '~') = 'S' THEN
              -- Was synced, fields just changed externally -> mark pending
              :NEW.TALLY_SYNC := 'U';
              :NEW.UPDATED_ON  := SYSDATE;
            ELSIF NVL(:NEW.TALLY_SYNC, '~') != 'S' THEN
              -- Was NULL or U, fields changed -> keep/set U
              :NEW.TALLY_SYNC := 'U';
              :NEW.UPDATED_ON  := SYSDATE;
            END IF;
            -- If :NEW.TALLY_SYNC = 'S' AND :OLD.TALLY_SYNC != 'S': 
            --   sync agent just synced this row -> respect the S, dont override
          END IF;
        END;
        """
        
        cursor.execute(sql)
        print("Successfully updated trigger C##COLLAGETEST.TRG_STUDENT_MARK_UNSYNCED to include STUDENT_STATUS")
        
        cursor.close()
        connection.close()
    except Exception as e:
        print("Error updating trigger:", str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
