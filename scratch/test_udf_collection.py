import requests
import xml.etree.ElementTree as ET
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>List of Ledgers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="List of Ledgers">
     <TYPE>Ledger</TYPE>
     <FETCH>Name</FETCH>
     <FETCH>Parent</FETCH>
     <FETCH>DATEOFLEAVING</FETCH>
     <FETCH>CLASSOFLEAVING</FETCH>
     <FETCH>IMDATEOFLEAVE</FETCH>
    </TDLUSERLIST>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

headers = {"Content-Type": "text/xml; charset=utf-8"}
print("Querying Tally...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
    response.raise_for_status()
    print("Retrieved response.")
    
    # Save a slice to inspect
    with open("scratch/collection_test.xml", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
    root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    
    count = 0
    for led in root.findall(".//LEDGER"):
        parent_el = led.find("PARENT")
        parent = parent_el.text.strip() if parent_el is not None and parent_el.text else ""
        if "LEFT" in parent.upper() or "PASS" in parent.upper():
            name = led.get("NAME") or led.find("NAME").text
            print(f"Ledger: {name} under Parent: {parent}")
            # print all children
            for child in led:
                print(f"  {child.tag}: {child.text}")
            count += 1
            if count >= 5:
                break
except Exception as e:
    print(f"Error: {e}")
