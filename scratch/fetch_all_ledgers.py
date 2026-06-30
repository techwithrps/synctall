import requests

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

headers = {"Content-Type": "text/xml; charset=utf-8"}
print("Requesting all Ledgers from Tally...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    xml_data = response.text
    print(f"Retrieved {len(xml_data)} bytes of XML.")
    
    # Save the full XML to a scratch file
    with open("/Users/twrps/Desktop/synctal/scratch/all_ledgers_live.xml", "w", encoding="utf-8") as f:
        f.write(xml_data)
    print("Saved all ledgers to scratch/all_ledgers_live.xml")
    
    # Search for radhey -91919
    import xml.etree.ElementTree as ET
    import re
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_data)
    root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    
    found = False
    for ledger in root.findall(".//LEDGER"):
        name = ledger.get("NAME") or ""
        if "radhey" in name or "91919" in name:
            found = True
            print(f"\n--- Found ledger: {name} ---")
            element_str = ET.tostring(ledger, encoding="utf-8").decode("utf-8")
            print(element_str)
            
    if not found:
        print("radhey -91919 not found in the exported ledgers!")
        
except Exception as e:
    print(f"Error: {e}")
