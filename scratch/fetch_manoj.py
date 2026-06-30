import requests

def fetch_manoj():
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
     <FETCH>*</FETCH>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="NameFilter">$Name = "manoj -91918" or $Name = "91918"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    res = requests.post("http://192.168.64.2:9000", data=payload, headers=headers)
    with open("scratch/manoj_tally_details.xml", "w", encoding="utf-8") as f:
        f.write(res.text)
    print("Manoj details fetched and saved to scratch/manoj_tally_details.xml")

fetch_manoj()
