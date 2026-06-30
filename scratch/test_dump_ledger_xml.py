import requests
import xml.etree.ElementTree as ET
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>Ledger</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""

print("Fetching List of Ledgers XML...")
res = requests.post("http://192.168.64.2:9000", data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=30)
xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', res.text)
# Remove numeric entity references like &#2; or &#x02; which break XML parsers
xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
try:
    root = ET.fromstring(xml_clean.strip())
    print(f"Root tag: {root.tag}")
    ledgers = root.findall(".//LEDGER")
    print(f"Total LEDGER elements found: {len(ledgers)}")
    
    found = False
    for led in ledgers:
        name_attr = led.get("NAME") or ""
        aliases = [n.text.strip() if n.text else "" for n in led.findall(".//NAME")]
        if name_attr.lower() == "rajesh-1223" or "1223" in aliases or name_attr == "1223":
            found = True
            print(f"Found ledger tag for Rajesh-1223:")
            print(ET.tostring(led, encoding="utf-8").decode("utf-8"))
            print("-" * 40)
            
    if not found:
        print("Could not find Rajesh-1223. First 2 LEDGERs:")
        for led in ledgers[:2]:
            print(ET.tostring(led, encoding="utf-8").decode("utf-8"))
except Exception as parse_err:
    print(f"Failed to parse XML: {parse_err}")
    print("Response text snippet:")
    print(res.text[:1000])
