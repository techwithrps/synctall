import requests

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>LedgerByName</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="LedgerByName">
     <TYPE>Ledger</TYPE>
     <FILTER>IsMatchingLedger</FILTER>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="IsMatchingLedger">$Name = "Atal Lingfa -GF/2021/8052" OR $Name = "GF/2021/8052"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

response = requests.post("http://192.168.64.2:9000", data=payload, headers={"Content-Type": "text/xml"})
print(response.text[:3000])
