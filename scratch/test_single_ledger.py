import requests
import xml.etree.ElementTree as ET

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>SingleLedgerCol</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="SingleLedgerCol">
     <TYPE>Ledger</TYPE>
     <FILTER>NameFilter</FILTER>
     <FETCH>Name</FETCH>
     <FETCH>Parent</FETCH>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="NameFilter">$Name = "Rajesh-1223" or $Name = "1223"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

print("Fetching Rajesh-1223 object...")
res = requests.post("http://192.168.64.2:9000", data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=30)
print("Response text:")
print(res.text)
