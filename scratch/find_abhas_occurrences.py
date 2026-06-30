import xml.etree.ElementTree as ET
import re

print("Reading Master.xml...")
with open("/Users/twrps/Desktop/synctal/Master.xml", "rb") as f:
    content = f.read().decode("utf-16")

# Clean control characters
xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
xml_clean = re.sub(r'&#\d+;', '', xml_clean)
xml_clean = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', xml_clean)

root = ET.fromstring(xml_clean.encode("utf-8"))

def search_element(elem, path=""):
    name = elem.tag
    current_path = f"{path}/{name}" if path else name
    
    text = (elem.text or "").strip()
    if "Abhas Srivastava" in text:
        print(f"Path: {current_path} = {text}")
        
    for child in elem:
        search_element(child, current_path)

print("\nSearching elements for 'Abhas Srivastava'...")
for ledger in root.findall(".//LEDGER"):
    ledger_name = ledger.get("NAME", "")
    if "Abhas Srivastava" in ledger_name:
        print(f"\n--- In Ledger: {ledger_name} ---")
        search_element(ledger)
