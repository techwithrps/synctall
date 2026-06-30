import requests

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

response = requests.post("http://192.168.64.2:9000", data=payload, headers={"Content-Type": "text/xml"})
print(response.text[:2000])
