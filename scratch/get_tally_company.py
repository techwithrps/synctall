import requests

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
    print(f"Querying Tally at {tally_url} for open companies...")
    r = requests.post(tally_url, data=payload, headers={"Content-Type": "text/xml"}, timeout=15)
    print("Status code:", r.status_code)
    print("Response:")
    print(r.text)
except Exception as e:
    print("Error:", e)
