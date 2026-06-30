import requests
import xml.etree.ElementTree as ET

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Import</TALLYREQUEST>
  <TYPE>Data</TYPE>
  <ID>All Masters</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
  </DESC>
  <DATA>
   <TALLYMESSAGE xmlns:UDF="TallyUDF">
    <LEDGER NAME="TESTSTUDENT -1234" ACTION="Create">
     <NAME>TESTSTUDENT -1234</NAME>
     <PARENT>Sundry Debtors</PARENT>
    </LEDGER>
   </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>"""

try:
    response = requests.post("http://192.168.64.2:9000", data=payload, timeout=10)
    print("STATUS:", response.status_code)
    print("RESPONSE:")
    print(response.text)
except Exception as e:
    print("ERROR:", e)
