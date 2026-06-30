import requests
import xml.etree.ElementTree as ET
import re

def fetch_ledger(name):
    payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>DATA</TYPE>
  <ID>Ledger</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVOBJECTNAME>{name}</SVOBJECTNAME>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error: {e}"

print("Fetching Atal Lingfa ledger...")
xml_data = fetch_ledger("Atal Lingfa -GF/2021/8052")

# Save to scratch
with open("scratch/atal_tally.xml", "w", encoding="utf-8") as f:
    f.write(xml_data)
print("Saved to scratch/atal_tally.xml")

# Parse and print all elements that have text content
xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_data)
xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
try:
    root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    for elem in root.iter():
        if elem.text and elem.text.strip() and len(elem.text.strip()) > 0 and elem.tag != "LEDGER" and not elem.tag.endswith("LIST"):
            print(f" - {elem.tag}: {elem.text.strip()}")
except Exception as e:
    print("XML Parsing error:", e)
