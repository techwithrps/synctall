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
print("Fetching live student details from Tally...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    xml_data = response.text
    print(f"Retrieved {len(xml_data)} bytes.")
    
    # Save live XML to scratch for inspection
    with open("scratch/live_student_details.xml", "w", encoding="utf-8") as f:
        f.write(xml_data)
        
    # Search for Aaliya
    import xml.etree.ElementTree as ET
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_data)
    root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    
    # Traverse sequentially or DFS to find Aaliya
    found = False
    current_student_tags = []
    
    # Let us do a simple string search in xml_clean to print lines around Aaliya
    lines = xml_clean.splitlines()
    for idx, line in enumerate(lines):
        if "212236DP001" in line or "Aaliya Bano" in line:
            found = True
            print(f"\n--- Found Aaliya Bano lines in XML (around line {idx}) ---")
            for j in range(max(0, idx-5), min(len(lines), idx+60)):
                print(f"{j+1}: {lines[j]}")
            break
            
    if not found:
        print("Aaliya Bano not found in live student details XML!")
except Exception as e:
    print(f"Error: {e}")
