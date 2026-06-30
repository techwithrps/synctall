import requests

def fetch_ledger(name):
    payload = f"""<ENVELOPE>
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
    <SVOBJECTNAME>{name}</SVOBJECTNAME>
   </STATICVARIABLES>
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

print("Fetching Abhas Srivastava ledger...")
abhas_xml = fetch_ledger("Abhas Srivastava -21258BP001")
with open("/Users/twrps/Desktop/synctal/scratch/abhas_tally.xml", "w", encoding="utf-8") as f:
    f.write(abhas_xml)
print("Saved to scratch/abhas_tally.xml")

print("Fetching radhey -91919 ledger...")
radhey_xml = fetch_ledger("radhey -91919")
with open("/Users/twrps/Desktop/synctal/scratch/radhey_tally.xml", "w", encoding="utf-8") as f:
    f.write(radhey_xml)
print("Saved to scratch/radhey_tally.xml")
