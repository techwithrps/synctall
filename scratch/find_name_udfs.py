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

print("\nSearching UDFs for name matches...")
for ledger in root.findall(".//LEDGER"):
    name = ledger.get("NAME", "")
    # Extract clean student name (everything before the first '-' or digit)
    parts = re.split(r'[-0-9]', name)
    clean_name = parts[0].strip() if parts else ""
    if len(clean_name) > 3:
        for child in ledger:
            if child.tag.startswith("{TallyUDF}"):
                val = child[0].text if len(child) > 0 else child.text
                val = (val or "").strip()
                if clean_name.lower() in val.lower():
                    print(f"Ledger: {name}")
                    print(f"  Tag: {child.tag.replace('{TallyUDF}', '')} = {val}")
