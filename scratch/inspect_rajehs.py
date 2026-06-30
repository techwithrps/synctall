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

for ledger in root.findall(".//LEDGER"):
    name = ledger.get("NAME", "")
    if "Rajehs" in name:
        print(f"Found ledger: {name}")
        for child in ledger:
            if child.tag.startswith("{TallyUDF}"):
                print(f"  UDF {child.tag.replace('{TallyUDF}', '')}: {child[0].text if len(child) > 0 else child.text}")
            else:
                text = (child.text or "").strip()
                if text and text not in ("No", "Not Applicable", "₹", "Others", "Regular", "Services"):
                    print(f"  Field {child.tag}: {text}")
