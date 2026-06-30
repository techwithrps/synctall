import requests
import sys

def fetch_ledger_xml(name):
    # Query using a Collection query with a filter for the ledger name
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
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="NameFilter">$Name = "{name}"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error: {e}"

print("Fetching live XML for shyam -8688...")
shyam_xml = fetch_ledger_xml("shyam -8688")
with open("/Users/twrps/Desktop/synctal/scratch/shyam_live.xml", "w", encoding="utf-8") as f:
    f.write(shyam_xml)
print("Saved to scratch/shyam_live.xml")

print("Fetching live XML for Abhas Srivastava...")
abhas_xml = fetch_ledger_xml("Abhas Srivastava -21258BP001")
with open("/Users/twrps/Desktop/synctal/scratch/abhas_live.xml", "w", encoding="utf-8") as f:
    f.write(abhas_xml)
print("Saved to scratch/abhas_live.xml")
