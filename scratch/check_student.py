import oracledb
from sync_agent.config import settings

def check_student():
    connection = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=settings.DB_CONNECT_STRING
    )
    cursor = connection.cursor()
    query = """
        SELECT ENRL_NO, STUDENT_NAME, BRANCH, SESSION_YEAR, STUDENT_MOBILE, TRN_STATUS, UPDATED_ON
        FROM C##COLLAGETEST.STUDENT_MASTER_DATA
        WHERE ENRL_NO = 'PGD/2022/5781'
    """
    cursor.execute(query)
    row = cursor.fetchone()
    if row:
        print("Oracle Student Details:")
        print(f"ENRL_NO: {row[0]}")
        print(f"Name: {row[1]}")
        print(f"Branch: {row[2]}")
        print(f"Session: {row[3]}")
        print(f"Mobile: {row[4]}")
        print(f"TRN_STATUS: {row[5]}")
        print(f"UPDATED_ON: {row[6]}")
    else:
        print("Student not found.")
    cursor.close()
    connection.close()

if __name__ == '__main__':
    check_student()
