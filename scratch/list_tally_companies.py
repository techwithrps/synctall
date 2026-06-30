import requests

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

response = requests.post("http://192.168.64.2:9000", data=payload, headers={"Content-Type": "text/xml"}, timeout=10)
print(response.text)
