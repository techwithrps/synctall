import requests

def fetch_object(name):
    payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>OBJECT</TYPE>
  <SUBTYPE>Ledger</SUBTYPE>
  <IDENTIFIER>{name}</IDENTIFIER>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
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

print("Fetching 91919 safely...")
radhey_xml = fetch_object("91919")
with open("/Users/twrps/Desktop/synctal/scratch/radhey_safe.xml", "w", encoding="utf-8") as f:
    f.write(radhey_xml)
print("Saved to scratch/radhey_safe.xml")
