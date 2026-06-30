import requests
import xml.etree.ElementTree as ET

url = "http://192.168.64.2:9000"
headers = {"Content-Type": "text/xml; charset=utf-8"}

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>List of Ledgers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="List of Ledgers">
     <TYPE>Ledger</TYPE>
     <FETCH>Name, Parent, MailingName</FETCH>
    </TDLUSERLIST>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

res = requests.post(url, data=payload, headers=headers)
root = ET.fromstring(res.text.strip())
ledgers = root.findall(".//LEDGER")
print(f"Total ledgers retrieved: {len(ledgers)}")
found = 0
for led in ledgers:
    name = led.get("NAME") or ""
    parent = led.find("PARENT")
    parent_name = parent.text if parent is not None else ""
    if "suyog" in name.lower() or "102" in name or "brijesh" in name.lower() or "10001" in name:
        print(f"Name: {name} | Parent: {parent_name}")
        found += 1

if found == 0:
    print("None of the synced names found in live Ledgers collection.")
    print("First 10 ledgers:")
    for led in ledgers[:10]:
        name = led.get("NAME") or ""
        parent = led.find("PARENT")
        parent_name = parent.text if parent is not None else ""
        print(f"  {name} (Parent: {parent_name})")
