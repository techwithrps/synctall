import requests
import xml.etree.ElementTree as ET
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>LeftStudentsCollection</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="LeftStudentsCollection">
     <TYPE>Ledger</TYPE>
     <CHILDSTATUS>Yes</CHILDSTATUS>
     <BELONGSTO>Yes</BELONGSTO>
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
print("Querying Tally for Left/Passout collection...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
    response.raise_for_status()
    print("Retrieved response. Length:", len(response.text))
    
    with open("scratch/left_collection.xml", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
    root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    
    count = 0
    for led in root.findall(".//LEDGER"):
        name = led.get("NAME") or led.find("NAME").text
        parent = led.find("PARENT").text if led.find("PARENT") is not None else ""
        print(f"Ledger: {name} (Parent: {parent})")
        for child in led:
            print(f"  {child.tag}: {child.text}")
        count += 1
        if count >= 10:
            break
except Exception as e:
    print(f"Error: {e}")
