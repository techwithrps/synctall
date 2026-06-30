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
    <SVCURRENTCOMPANY>100000</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""

url = "http://103.107.67.50:9001/"
try:
    response = requests.post(url, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=15)
    print("Response Status:", response.status_code)
    print("Response Body:\n", response.text)
except Exception as e:
    print("Error querying Tally:", e)
