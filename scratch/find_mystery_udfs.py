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

print("\nScanning ledgers for mystery UDFs...")
count = 0
for ledger in root.findall(".//LEDGER"):
    udf1 = ledger.find(".//{TallyUDF}_UDF_553648475")
    udf2 = ledger.find(".//{TallyUDF}_UDF_788529458")
    udf3 = ledger.find(".//{TallyUDF}_UDF_805327489")
    
    if udf1 is not None or udf2 is not None or udf3 is not None:
        name = ledger.get("NAME", "")
        val1 = udf1.text if udf1 is not None else "None"
        val2 = udf2.text if udf2 is not None else "None"
        val3 = udf3.text if udf3 is not None else "None"
        print(f"Ledger: {name}")
        print(f"  _UDF_553648475: {val1}")
        print(f"  _UDF_788529458: {val2}")
        print(f"  _UDF_805327489: {val3}")
        count += 1
        if count >= 15:
            break
