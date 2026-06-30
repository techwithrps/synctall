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

udf_tags = set()
for ledger in root.findall(".//LEDGER"):
    for child in ledger:
        if child.tag.startswith("{TallyUDF}"):
            udf_tags.add((child.tag, child.get("desc") or ""))

print("\n--- ALL UNIQUE UDF TAGS IN ALL LEDGERS ---")
for tag, desc in sorted(udf_tags):
    print(f"Tag: {tag.replace('{TallyUDF}', '')} | Description: {desc}")
