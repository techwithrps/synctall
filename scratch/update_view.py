import os
import httpx
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Missing credentials")
    exit(1)

with open('supabase/migrations/20260525000001_student_ledger_vouchers.sql', 'r') as f:
    sql = f.read()

# Execute SQL directly via PostgREST RPC (if available) or using the Supabase API
# Note: Since the postgres connection string is not in .env, we can just print the SQL
# and instruct the user to run it, OR if there's a psycopg2 module, we could use that.
# Actually, the user has the Supabase SQL editor open right in their screenshot!
print("Please run the SQL file content in Supabase.")
