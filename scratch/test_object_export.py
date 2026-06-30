import requests

def fetch_object_by_xml(name):
    payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>OBJECT</TYPE>
  <SUBTYPE>Ledger</SUBTYPE>
  <ID>{name}</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    payload_opt2 = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT DATA</TALLYREQUEST>
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
    
    print("Trying Option 1 (<ID> tag)...")
    res1 = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
    print("Option 1 response:")
    print(res1.text[:500])
    print("-" * 50)
    
    print("Trying Option 2 (IDENTIFIER with EXPORT DATA)...")
    res2 = requests.post("http://192.168.64.2:9000", data=payload_opt2, headers=headers, timeout=10)
    print("Option 2 response:")
    print(res2.text[:500])
    print("-" * 50)

fetch_object_by_xml("Abhas Srivastava -21258BP001")
