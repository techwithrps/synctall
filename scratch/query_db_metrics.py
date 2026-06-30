import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sync_agent.oracle_client import OracleSyncClient

client = OracleSyncClient()
conn = client._get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT 
        SUM(CASE WHEN TALLY_SYNC = 'S' THEN 1 ELSE 0 END),
        SUM(CASE WHEN TALLY_SYNC = 'U' OR TALLY_SYNC = ' ' THEN 1 ELSE 0 END),
        SUM(CASE WHEN TALLY_SYNC IS NULL THEN 1 ELSE 0 END),
        SUM(CASE WHEN STUDENT_STATUS = 'L' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ') THEN 1 ELSE 0 END),
        SUM(CASE WHEN STUDENT_STATUS = 'P' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ') THEN 1 ELSE 0 END)
    FROM C##COLLAGETEST.STUDENT_MASTER_DATA
""")
row = cur.fetchone()
print(row)
cur.close()
conn.close()

