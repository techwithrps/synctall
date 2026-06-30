import requests
import xml.etree.ElementTree as ET
import re

payload = """<ENVELOPE>
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
    <SVOBJECTNAME>Atal Lingfa -GF/2021/8052</SVOBJECTNAME>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""

headers = {"Content-Type": "text/xml; charset=utf-8"}
response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
if response.status_code == 200:
    print("SUCCESS! Standard Ledger XML for Atal Lingfa:")
    # Print lines that have ADDRESS, EMAIL, parent, or name
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
    print(xml_clean)
else:
    print("FAILED:", response.status_code)
