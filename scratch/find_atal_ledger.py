import requests
import xml.etree.ElementTree as ET
import re

tally_url = "http://192.168.64.2:9000"

def fetch_all_ledgers():
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
    </TDLUSERLIST>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(tally_url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text
        
        # Clean invalid characters
        xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
        xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
        root = ET.fromstring(xml_clean.strip().encode('utf-8'))
        
        print("Searching for ledgers matching '8052' or 'Atal':")
        found = False
        for led in root.findall(".//LEDGER"):
            name = led.get("NAME")
            if not name:
                continue
            name_lower = name.lower()
            if "8052" in name_lower or "atal" in name_lower:
                found = True
                print(f"Ledger Name: {name}")
                # Print names list
                for name_elem in led.findall(".//NAME"):
                    if name_elem.text:
                        print(f" - Alias/Alt Name: {name_elem.text.strip()}")
                        
        if not found:
            print("No matching ledgers found in the whole List of Ledgers!")
            
    except Exception as e:
        print(f"Error: {e}")

fetch_all_ledgers()
