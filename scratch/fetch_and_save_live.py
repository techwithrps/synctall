import requests
import xml.etree.ElementTree as ET
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
print("Querying Tally StudentDetail...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=20)
    response.raise_for_status()
    print("Retrieved response successfully.")
    
    # Clean control characters
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
    
    # Save the file
    with open("scratch/live_student_details.xml", "w", encoding="utf-8") as f:
        f.write(xml_clean)
    print("Saved to scratch/live_student_details.xml")
    
    # Search for Aaliya Bano record
    lines = xml_clean.splitlines()
    found = False
    for idx, line in enumerate(lines):
        if "212236DP001" in line or "Aaliya Bano" in line:
            found = True
            print(f"\n--- Found Aaliya Bano lines in XML (around line {idx}) ---")
            for j in range(max(0, idx-2), min(len(lines), idx+50)):
                print(f"{j+1}: {lines[j]}")
            break
    if not found:
        print("Aaliya Bano not found in live XML!")
except Exception as e:
    print(f"Error: {e}")
