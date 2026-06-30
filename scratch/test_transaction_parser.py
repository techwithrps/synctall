import sys
sys.path.append("/Users/twrps/Desktop/synctal")
from sync_agent.parser import parse_transactions_xml

def test_parser():
    try:
        with open('Transactions.xml', 'r', encoding='utf-16') as f:
            xml_data = f.read()
    except UnicodeDecodeError:
        with open('Transactions.xml', 'r', encoding='utf-8-sig') as f:
            xml_data = f.read()

    print("Parsing Transactions.xml...")
    transactions = parse_transactions_xml(xml_data)
    print(f"Parsed {len(transactions)} fee transactions.")
    
    if transactions:
        print("\n--- FIRST TRANSACTION ---")
        tx = transactions[0]
        for k, v in tx.items():
            if k == 'raw_payload':
                print(f"{k}: <omitted for brevity>")
            else:
                print(f"{k}: {v}")
                
if __name__ == "__main__":
    test_parser()
