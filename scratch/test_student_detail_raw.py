import requests

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
    <SVCURRENTCOMPANY>Demo Data College</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""

response = requests.post("http://192.168.64.2:9000", data=payload, headers={"Content-Type": "text/xml"}, timeout=15)
print("Status Code:", response.status_code)
print("Length of Response:", len(response.text))
print("First 1000 chars:")
print(response.text[:1000])
