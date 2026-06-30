import requests

url = "http://192.168.64.2:9000"
headers = {"Content-Type": "text/xml; charset=utf-8"}

# Let's craft the corrected XML for shyam -8688
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
    <LEDGER NAME="8688" ACTION="Alter">
     <OLDMAILINGNAME.LIST TYPE="String">
      <OLDMAILINGNAME>shyam</OLDMAILINGNAME>
     </OLDMAILINGNAME.LIST>
     <LANGUAGENAME.LIST>
      <NAME.LIST TYPE="String">
       <NAME>shyam -8688</NAME>
       <NAME>8688</NAME>
      </NAME.LIST>
      <LANGUAGEID>1033</LANGUAGEID>
     </LANGUAGENAME.LIST>
     <MAILINGNAME>shyam</MAILINGNAME>
     <PARENT>BBA 1ST YEAR Sem-1</PARENT>
     <OPENINGBALANCE>-80000.00</OPENINGBALANCE>
     <ISBILLWISEON>Yes</ISBILLWISEON>
     <LEDMAILINGDETAILS.LIST>
      <APPLICABLEFROM>20220401</APPLICABLEFROM>
      <MAILINGNAME>shyam</MAILINGNAME>
      <STATE>Uttar Pradesh</STATE>
      <COUNTRY>India</COUNTRY>
     </LEDMAILINGDETAILS.LIST>
    </LEDGER>
   </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>"""

print("Sending corrected XML payload for shyam -8688 to Tally...")
try:
    res = requests.post(url, data=payload, headers=headers, timeout=10)
    print("Status Code:", res.status_code)
    print("Response text:")
    print(res.text)
except Exception as e:
    print("Error:", e)
