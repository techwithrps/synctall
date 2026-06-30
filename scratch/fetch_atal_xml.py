import requests
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>Ledger</ID>
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
print("Requesting all Ledgers from Tally...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    xml_data = response.text
    print(f"Retrieved {len(xml_data)} bytes of XML.")
    
    # Save raw XML
    with open("scratch/all_ledgers_raw_fetch.xml", "w", encoding="utf-8") as f:
        f.write(xml_data)
    print("Saved to scratch/all_ledgers_raw_fetch.xml")
    
    # Find ledger block with regex
    # We look for <LEDGER NAME="Atal Lingfa -GF/2021/8052" ...> ... </LEDGER>
    # Since XML tags can span multiple lines, let's use re.DOTALL
    pattern = r'(<LEDGER[^>]*NAME="[^"]*Atal Lingfa[^"]*"[^>]*>.*?</LEDGER>)'
    matches = re.findall(pattern, xml_data, re.DOTALL)
    if matches:
        for idx, match in enumerate(matches):
            print(f"\nMatch {idx+1}:")
            print(match[:2000]) # Print first 2000 chars of match
            with open(f"scratch/atal_ledger_regex_match_{idx}.xml", "w", encoding="utf-8") as f:
                f.write(match)
            print(f"Saved match {idx} to scratch/atal_ledger_regex_match_{idx}.xml")
    else:
        print("Atal Lingfa not found using regex pattern!")
        
except Exception as e:
    print(f"Error: {e}")
