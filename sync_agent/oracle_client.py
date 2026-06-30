import oracledb
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .config import settings
from .logger import setup_logger

logger = setup_logger("oracle_client", settings.LOG_LEVEL)

class OracleSyncClient:
    def __init__(self):
        """
        Initializes Oracle DB client targeting the configured connection string.
        """
        self.user = settings.DB_USER
        self.password = settings.DB_PASSWORD
        self.dsn = settings.DB_CONNECT_STRING
        logger.info(f"Initializing Oracle DB client targeting: {self.dsn}")

    def _get_connection(self):
        return oracledb.connect(
            user=self.user,
            password=self.password,
            dsn=self.dsn
        )

    def get_all_students(self) -> List[Dict[str, Any]]:
        """
        Fetches student details from STUDENT_MASTER_DATA.
        """
        connection = None
        cursor = None
        students = []
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            query = f"""
                SELECT ENRL_NO, STUDENT_NAME, BRANCH, ROLL_NO, REG_NO, COURSE, 
                       SESSION_YEAR, FATHER_NAME, MOTHER_NAME, STUDENT_GENDER, 
                       STUDENT_MOBILE, STUDENT_EMAIL_ID, CURRENT_ADDRESS, ACTIVE_STATUS_ID,
                       STUDENT_DOB, STUDENT_CATEGORY, STUDENT_RELIGION, STUDENT_CASTE,
                       STUDENT_QUOTA, PERMANENT_ADDRESS, PERMANENT_PIN, CURRENT_PIN,
                       STUDENT_STATUS, COMPANY_ID
                FROM {settings.DB_SCHEMA}.STUDENT_MASTER_DATA
                WHERE ENRL_NO IS NOT NULL
                  AND COMPANY_ID = {settings.DB_COMPANY_ID}
            """
            cursor.execute(query)
            col_names = [col[0].lower() for col in cursor.description]
            for row in cursor.fetchall():
                student_row = dict(zip(col_names, row))
                # Map Oracle column names back to standard codebase names
                mapped_row = {
                    "enrollment_no": student_row.get("enrl_no"),
                    "student_name": student_row.get("student_name"),
                    "student_class": student_row.get("branch"),
                    "roll_no": student_row.get("roll_no"),
                    "registration_no": student_row.get("reg_no"),
                    "course": student_row.get("course"),
                    "session": student_row.get("session_year"),
                    "father_name": student_row.get("father_name"),
                    "mother_name": student_row.get("mother_name"),
                    "gender": student_row.get("student_gender"),
                    "mobile": student_row.get("student_mobile"),
                    "email": student_row.get("student_email_id"),
                    "correspondence_address": student_row.get("current_address") if student_row.get("current_address") else student_row.get("permanent_address"),
                    "permanent_address": student_row.get("permanent_address") if student_row.get("permanent_address") else student_row.get("current_address"),
                    "dob": student_row.get("student_dob"),
                    "category": student_row.get("student_category"),
                    "religion": student_row.get("student_religion"),
                    "caste": student_row.get("student_caste"),
                    "quota": student_row.get("student_quota"),
                    "permanent_pin": student_row.get("permanent_pin"),
                    "correspondence_pin": student_row.get("current_pin"),
                    "status": student_row.get("student_status"),
                    "is_left": (str(student_row.get("student_status") or "").strip().upper() in ('P', 'L')) or (student_row.get("active_status_id") == 0),
                    "company_id": student_row.get("company_id")
                }
                students.append(mapped_row)
            return students
        except Exception as e:
            logger.error(f"Failed to fetch students from Oracle: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def upsert_students_batch(self, students: List[Dict[str, Any]], job_id: str = None) -> Tuple[int, int]:
        """
        Upserts a batch of students using MERGE INTO.
        """
        processed_count = 0
        failed_count = 0
        
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            merge_query = f"""
                MERGE INTO {settings.DB_SCHEMA}.STUDENT_MASTER_DATA target
                USING (
                  SELECT :enrl_no AS enrl_no FROM dual
                ) source
                ON (target.ENRL_NO = source.enrl_no)
                WHEN MATCHED THEN
                  UPDATE SET 
                    target.STUDENT_NAME = :student_name,
                    target.STUDENT_GENDER = :student_gender,
                    target.STUDENT_MOBILE = :student_mobile,
                    target.STUDENT_EMAIL_ID = :student_email_id,
                    target.COURSE = :course,
                    target.BRANCH = :student_class,
                    target.SESSION_YEAR = :session_year,
                    target.FATHER_NAME = :father_name,
                    target.MOTHER_NAME = :mother_name,
                    target.ROLL_NO = :roll_no,
                    target.REG_NO = :registration_no,
                    target.ACTIVE_STATUS_ID = :active_status_id,
                    target.UPDATED_ON = SYSDATE,
                    target.UPDATED_BY = 'TALLY_SYNC',
                    target.DATA_UPDATED_DATE = SYSDATE
                WHEN NOT MATCHED THEN
                  INSERT (
                    STUDENT_ID, ENRL_NO, CRN, STUDENT_NAME, STUDENT_GENDER, STUDENT_MOBILE, STUDENT_EMAIL_ID,
                    COURSE, BRANCH, SESSION_YEAR, FATHER_NAME, MOTHER_NAME, ROLL_NO, REG_NO, ACTIVE_STATUS_ID,
                    CREATED_ON, CREATED_BY, UPDATED_ON, UPDATED_BY
                  ) VALUES (
                    {settings.DB_SCHEMA}.STUDENT_ID.NEXTVAL,
                    :enrl_no, :enrl_no, :student_name, :student_gender, :student_mobile, :student_email_id,
                    :course, :student_class, :session_year, :father_name, :mother_name, :roll_no, :registration_no, :active_status_id,
                    SYSDATE, 'TALLY_SYNC', SYSDATE, 'TALLY_SYNC'
                  )
            """
            
            for s in students:
                try:
                    # Prepare bind variables
                    # Active status is 0 if student has left, otherwise 1 (active)
                    active_status_id = 0 if s.get("is_left") else 1
                    
                    bind_vars = {
                        "enrl_no": str(s.get("enrollment_no", "")).strip(),
                        "student_name": str(s.get("student_name", "Unknown Student")).strip()[:100],
                        "student_gender": str(s.get("gender", "")).strip()[:10],
                        "student_mobile": str(s.get("mobile", "")).strip()[:15],
                        "student_email_id": str(s.get("email", "")).strip()[:50],
                        "course": str(s.get("course", "")).strip()[:100],
                        "student_class": str(s.get("student_class", "")).strip()[:100],
                        "session_year": str(s.get("session", "")).strip()[:20],
                        "father_name": str(s.get("father_name", "")).strip()[:100],
                        "mother_name": str(s.get("mother_name", "")).strip()[:100],
                        "roll_no": str(s.get("roll_no", "")).strip()[:20],
                        "registration_no": str(s.get("registration_no", "")).strip()[:50],
                        "active_status_id": active_status_id
                    }
                    
                    cursor.execute(merge_query, bind_vars)
                    processed_count += 1
                except Exception as row_err:
                    failed_count += 1
                    logger.error(f"Record upsert failed in Oracle for {s.get('enrollment_no')}: {str(row_err)}")
                    
            connection.commit()
            return processed_count, failed_count
        except Exception as e:
            logger.error(f"Oracle bulk upsert operation failed: {str(e)}")
            if connection:
                connection.rollback()
            return processed_count, len(students) - processed_count
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_recently_updated_students(self, last_sync_time=None) -> List[Dict[str, Any]]:
        """
        Fetches student details from STUDENT_MASTER_DATA that need to be synced to Tally.
        Picks up:
          - TALLY_SYNC IS NULL  => New student, never synced
          - TALLY_SYNC = 'U'   => Field changed, re-sync needed
          - TALLY_SYNC = ' '   => Legacy blank value treated as unsynced
        Does NOT rely on UPDATED_ON timestamp anymore — purely TALLY_SYNC driven.
        """
        connection = None
        cursor = None
        students = []
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            query = f"""
                SELECT ENRL_NO, STUDENT_NAME, BRANCH, ROLL_NO, REG_NO, COURSE, 
                       SESSION_YEAR, FATHER_NAME, MOTHER_NAME, STUDENT_GENDER, 
                       STUDENT_MOBILE, STUDENT_EMAIL_ID, CURRENT_ADDRESS, ACTIVE_STATUS_ID, UPDATED_ON,
                       STUDENT_DOB, STUDENT_CATEGORY, STUDENT_RELIGION, STUDENT_CASTE,
                       STUDENT_QUOTA, PERMANENT_ADDRESS, PERMANENT_PIN, CURRENT_PIN,
                       STUDENT_STATUS, COMPANY_ID
                FROM {settings.DB_SCHEMA}.STUDENT_MASTER_DATA
                WHERE ENRL_NO IS NOT NULL
                  AND COMPANY_ID = {settings.DB_COMPANY_ID}
                  AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ' OR (TALLY_SYNC IS NULL AND CREATED_ON >= SYSDATE - 1))
                ORDER BY CASE WHEN STUDENT_STATUS IN ('P', 'L') OR ACTIVE_STATUS_ID = 0 THEN 2 ELSE 1 END ASC,
                         CASE WHEN TALLY_SYNC = 'U' THEN 1 ELSE 2 END ASC,
                         UPDATED_ON DESC NULLS LAST,
                         CREATED_ON DESC NULLS LAST
            """
            cursor.execute(query)
            col_names = [col[0].lower() for col in cursor.description]
            for row in cursor.fetchall():
                student_row = dict(zip(col_names, row))
                mapped_row = {
                    "enrollment_no": student_row.get("enrl_no"),
                    "student_name": student_row.get("student_name"),
                    "student_class": student_row.get("branch"),
                    "roll_no": student_row.get("roll_no"),
                    "registration_no": student_row.get("reg_no"),
                    "course": student_row.get("course"),
                    "session": student_row.get("session_year"),
                    "father_name": student_row.get("father_name"),
                    "mother_name": student_row.get("mother_name"),
                    "gender": student_row.get("student_gender"),
                    "mobile": student_row.get("student_mobile"),
                    "email": student_row.get("student_email_id"),
                    "correspondence_address": student_row.get("current_address") if student_row.get("current_address") else student_row.get("permanent_address"),
                    "permanent_address": student_row.get("permanent_address") if student_row.get("permanent_address") else student_row.get("current_address"),
                    "dob": student_row.get("student_dob"),
                    "category": student_row.get("student_category"),
                    "religion": student_row.get("student_religion"),
                    "caste": student_row.get("student_caste"),
                    "quota": student_row.get("student_quota"),
                    "permanent_pin": student_row.get("permanent_pin"),
                    "correspondence_pin": student_row.get("current_pin"),
                    "status": student_row.get("student_status"),
                    "is_left": (str(student_row.get("student_status") or "").strip().upper() in ('P', 'L')) or (student_row.get("active_status_id") == 0),
                    "updated_on": student_row.get("updated_on"),
                    "company_id": student_row.get("company_id")
                }
                students.append(mapped_row)
            return students
        except Exception as e:
            logger.error(f"Failed to fetch recently updated students from Oracle: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def update_tally_sync_status(self, enrl_no: str, status: str = 'S') -> None:
        """
        Updates TALLY_SYNC column in STUDENT_MASTER_DATA — our dedicated sync tracking column.
        - 'S' = Synced to Tally successfully
        - 'U' = Updated/pending — needs to be pushed to Tally
        - NULL = New student, never synced
        Note: Does NOT touch TRN_STATUS (used by other systems).
        """
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            query = f"""
                UPDATE {settings.DB_SCHEMA}.STUDENT_MASTER_DATA
                SET TALLY_SYNC = :status
                WHERE ENRL_NO = :enrl_no
            """
            cursor.execute(query, {"status": status, "enrl_no": enrl_no})
            connection.commit()
            logger.info(f"TALLY_SYNC set to '{status}' for enrollment: {enrl_no}")
        except Exception as e:
            logger.error(f"Failed to update TALLY_SYNC for enrollment {enrl_no}: {str(e)}")
            if connection:
                connection.rollback()
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def mark_students_unsynced(self, enrl_nos: list = None) -> int:
        """
        Marks one or more students (or ALL if enrl_nos is None) as TALLY_SYNC='U'
        so they will be picked up in the next sync cycle.
        Returns the count of rows updated.
        """
        connection = None
        cursor = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            if enrl_nos:
                updated = 0
                for enrl_no in enrl_nos:
                    cursor.execute(
                        f"UPDATE {settings.DB_SCHEMA}.STUDENT_MASTER_DATA SET TALLY_SYNC = 'U' WHERE ENRL_NO = :enrl_no",
                        {"enrl_no": enrl_no}
                    )
                    updated += cursor.rowcount
                connection.commit()
                logger.info(f"Marked {updated} students as TALLY_SYNC='U' (pending sync) in Oracle.")
                return updated
            else:
                cursor.execute(
                    f"UPDATE {settings.DB_SCHEMA}.STUDENT_MASTER_DATA SET TALLY_SYNC = 'U' WHERE TALLY_SYNC = 'S'"
                )
                updated = cursor.rowcount
                connection.commit()
                logger.info(f"Bulk marked {updated} students as TALLY_SYNC='U' for full re-sync.")
                return updated
        except Exception as e:
            logger.error(f"Failed to mark students as unsynced in Oracle: {str(e)}")
            if connection:
                connection.rollback()
            return 0
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

