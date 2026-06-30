import requests

url = "http://192.168.64.2:9000"
headers = {"Content-Type": "text/xml; charset=utf-8"}

# Let's craft the exact XML sent by tally_client for 102
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
    <LEDGER NAME="102" ACTION="Alter">
     <NAME.LIST TYPE="String">
      <NAME>suyog system -102</NAME>
      <NAME>102</NAME>
     </NAME.LIST>
     <OPENINGBALANCE>0.00</OPENINGBALANCE>
     <ISBILLWISEON>No</ISBILLWISEON>
    </LEDGER>
   </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>"""

print("Sending import payload to Tally...")
res = requests.post(url, data=payload, headers=headers)
print("Status Code:", res.status_code)
print("Response text:")
print(res.text)
