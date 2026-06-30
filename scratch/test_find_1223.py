import sys
sys.path.append("/Users/twrps/Desktop/synctal")

from sync_agent.tally_client import TallyClient

print("Initializing Tally Client...")
client = TallyClient()

print("Fetching all ledgers with parent...")
try:
    ledger_parents = client.fetch_all_ledgers_with_parent()
    print(f"Total entries fetched: {len(ledger_parents)}")
    matches = {k: v for k, v in ledger_parents.items() if "1223" in k}
    print(f"Matches for '1223':")
    for k, v in matches.items():
        print(f"  {k} -> {v}")
except Exception as e:
    print(f"ERROR: {e}")
