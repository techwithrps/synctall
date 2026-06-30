import requests
import xml.etree.ElementTree as ET
import re

tally_url = "http://192.168.64.2:9000"

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>DATA</TYPE>
  <ID>StudentDetail</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""

print("Fetching all student details from Tally...")
response = requests.post(tally_url, data=payload, headers={"Content-Type": "text/xml"})
if response.status_code == 200:
    content = response.text
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
    xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
    
    # Save raw student details for debugging
    with open("scratch/student_details_raw.xml", "w", encoding="utf-8") as f:
        f.write(content)
        
    root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    
    # Search for GF/2021/8052 in LEDGER nodes
    for ledger in root.findall(".//LEDGER"):
        name = ledger.get("NAME")
        # Check alias
        aliases = [n.text.strip() for n in ledger.findall(".//NAME") if n.text]
        if "GF/2021/8052" in aliases or name == "Atal Lingfa -GF/2021/8052" or "GF/2021/8052" in name:
            print("\nFOUND LEDGER IN TALLY STUDENT DETAILS EXPORT:")
            print("Ledger Name:", name)
            print("Aliases:", aliases)
            parent = ledger.find("PARENT")
            print("Parent/Group:", parent.text if parent is not None else "None")
            
            # Print all text nodes under LEDGER
            for elem in ledger.iter():
                if elem.text and elem.text.strip() and len(elem.text.strip()) > 0 and elem.tag != "LEDGER" and not elem.tag.endswith("LIST"):
                    print(f" - {elem.tag}: {elem.text.strip()}")
else:
    print(f"Failed to fetch. Status code: {response.status_code}")
