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

print("\nScanning ledgers...")
count = 0
for ledger in root.findall(".//LEDGER"):
    udf1 = ledger.find(".//{TallyUDF}_UDF_553648474")
    udf2 = ledger.find(".//{TallyUDF}_UDF_788529494")
    
    if udf1 is not None or udf2 is not None:
        name = ledger.get("NAME", "")
        val1 = udf1.text if udf1 is not None else "None"
        val2 = udf2.text if udf2 is not None else "None"
        print(f"Ledger: {name}")
        print(f"  _UDF_553648474 (Student Name?): {val1}")
        print(f"  _UDF_788529494 (Mailing Name?): {val2}")
        count += 1
        if count >= 10:
            break
