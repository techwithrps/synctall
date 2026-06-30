import requests
import xml.etree.ElementTree as ET
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>SingleLedger</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="SingleLedger">
     <TYPE>Ledger</TYPE>
     <FILTER>NameFilter</FILTER>
     <FETCH>*</FETCH>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formula" NAME="NameFilter">$Name = "Atal Lingfa -GF/2021/8052"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

headers = {"Content-Type": "text/xml; charset=utf-8"}
response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
if response.status_code == 200:
    print("SUCCESS! Full Ledger XML for Atal Lingfa:")
    # Print the full XML
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
    print(xml_clean)
else:
    print("FAILED:", response.status_code)
