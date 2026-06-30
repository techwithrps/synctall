import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sync_agent.oracle_client import OracleSyncClient

def test():
    client = OracleSyncClient()
    conn = client._get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM C##COLLAGETEST.STUDENT_MASTER_DATA WHERE COMPANY_ID = 10 AND (TALLY_SYNC IS NULL OR TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')")
    print(f"Total count (without enrl_no check): {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(1) FROM C##COLLAGETEST.STUDENT_MASTER_DATA WHERE ENRL_NO IS NOT NULL AND COMPANY_ID = 10 AND (TALLY_SYNC IS NULL OR TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')")
    print(f"Total count (with enrl_no IS NOT NULL check): {cur.fetchone()[0]}")

if __name__ == '__main__':
    test()
