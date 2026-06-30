import re

print("Reading Master.xml...")
with open("/Users/twrps/Desktop/synctal/Master.xml", "rb") as f:
    content = f.read().decode("utf-16")

# Clean control characters
xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
xml_clean = re.sub(r'&#\d+;', '', xml_clean)
xml_clean = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', xml_clean)

ledger_tag_start = xml_clean.find('<LEDGER NAME="AAFREEN FATMA -20258BP001"')
if ledger_tag_start != -1:
    ledger_tag_end = xml_clean.find('</LEDGER>', ledger_tag_start) + len('</LEDGER>')
    ledger_xml = xml_clean[ledger_tag_start:ledger_tag_end]
    
    with open("/Users/twrps/Desktop/synctal/scratch/aafreen_extracted.xml", "w", encoding="utf-8") as out:
        out.write(ledger_xml)
    print("Found and extracted to scratch/aafreen_extracted.xml")
else:
    print("Could not find ledger for Aafreen")
