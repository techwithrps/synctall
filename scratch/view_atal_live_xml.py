import requests
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>DATA</TYPE>
  <ID>StudentDetail</ID>
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
response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=20)
if response.status_code == 200:
    content = response.text
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
    
    # Let's search for "GF/2021/8052" or "Atal" and print the surrounding tags (2000 chars)
    idx = xml_clean.find("GF/2021/8052")
    if idx != -1:
        print("Atal Lingfa live XML block:")
        # Find start of student (approx by looking back for <KGSERIALNO>)
        start_idx = xml_clean.rfind("<KGSERIALNO>", 0, idx)
        if start_idx == -1:
            start_idx = max(0, idx - 500)
        # Find end of student by looking forward for the next <KGSERIALNO>
        end_idx = xml_clean.find("<KGSERIALNO>", idx)
        if end_idx == -1:
            end_idx = min(len(xml_clean), idx + 1500)
        print(xml_clean[start_idx:end_idx])
    else:
        print("Atal Lingfa not found by enrollment number in XML.")
