import requests
import sys

url = "http://192.168.64.2:9000"
headers = {"Content-Type": "text/xml; charset=utf-8"}

def query_ledger(name):
    payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>CustomLedgerCol</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="CustomLedgerCol">
     <TYPE>Ledger</TYPE>
     <FILTER>NameFilter</FILTER>
     <FETCH>*</FETCH>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="NameFilter">$Name = "{name}" or $Name = "{name.lower()}"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=60)
        res.raise_for_status()
        print(f"--- QUERY FOR: {name} ---")
        print(res.text)
    except Exception as e:
        print(f"Error querying {name}: {e}")

if len(sys.argv) > 1:
    query_ledger(sys.argv[1])
else:
    query_ledger("shyam -8688")
    query_ledger("Abhas Srivastava -21258BP001")
