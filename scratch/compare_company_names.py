import requests
import xml.etree.ElementTree as ET

tally_url = "http://103.107.67.58:9631/"
payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>ListofCompanies</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="ListofCompanies">
     <TYPE>Company</TYPE>
    </TDLUSERLIST>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

try:
    r = requests.post(tally_url, data=payload, headers={"Content-Type": "text/xml"}, timeout=15)
    root = ET.fromstring(r.text.strip())
    companies = root.findall(".//COMPANY")
    
    config_name = "SHOOLINI UNIVERSITY SOLAN (DISTANCE EDUCATION)"
    print(f"Configured name in .env: '{config_name}' (len: {len(config_name)})")
    
    for comp in companies:
        print("Attributes:", comp.attrib)
        # Check sub-elements as well
        for child in comp:
            print(f"  Child tag: {child.tag}, text: '{child.text}', attrib: {child.attrib}")
            
except Exception as e:
    print("Error:", e)
