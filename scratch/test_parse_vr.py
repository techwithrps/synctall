import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sync_agent.parser import parse_transactions_xml

def test_parse():
    with open("scratch/voucher_register_out.xml", "r", encoding="utf-8") as f:
        content = f.read()
    
    txs = parse_transactions_xml(content)
    print(f"Successfully parsed {len(txs)} transactions!")
    if len(txs) > 0:
        print("First tx:", txs[0])

if __name__ == "__main__":
    test_parse()
