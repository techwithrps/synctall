import requests
import xml.etree.ElementTree as ET
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>LeftLedgerCollection</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="LeftLedgerCollection">
     <TYPE>Ledger</TYPE>
     <FILTER>LeftGroupFilter</FILTER>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formula" NAME="LeftGroupFilter">$Parent = "Left 2026"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
headers = {"Content-Type": "text/xml; charset=utf-8"}

print("Requesting LeftLedgerCollection...")
try:
    res = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=30)
    res.raise_for_status()
    xml_data = res.text
    print(f"SUCCESS! Retrieved {len(xml_data)} bytes of XML.")
    
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_data)
    root = ET.fromstring(xml_clean.strip())

    ledgers = root.findall(".//LEDGER")
    print(f"Total ledgers found under group 'Left 2026': {len(ledgers)}")
    for led in ledgers:
        name_attr = led.get("NAME") or ""
        print(f"  - Ledger Name: {name_attr}")
except Exception as e:
    print(f"ERROR: {e}")
