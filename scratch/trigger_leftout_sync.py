import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sync_agent.oracle_client import OracleSyncClient
from sync_agent.tally_client import TallyClient

# Ensure Left 2026 group exists
tally = TallyClient()
tally.create_group_in_tally("Left 2026")

client = OracleSyncClient()
conn = client._get_connection()
cur = conn.cursor()

# Set TALLY_SYNC = 'U' for all left out and passed out students
cur.execute("""
    UPDATE C##COLLAGETEST.STUDENT_MASTER_DATA
    SET TALLY_SYNC = 'U'
    WHERE STUDENT_STATUS IN ('L', 'P') AND (TALLY_SYNC = 'S' OR TALLY_SYNC IS NULL)
""")
updated_rows = cur.rowcount
conn.commit()

print(f"Successfully marked {updated_rows} left out / passed out students as pending ('U') for sync.")

cur.close()
conn.close()
