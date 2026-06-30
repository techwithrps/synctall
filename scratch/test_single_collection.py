import requests
import xml.etree.ElementTree as ET
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>SingleLedgerCollection</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="SingleLedgerCollection">
     <TYPE>Ledger</TYPE>
     <FILTER>NameFilter</FILTER>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formula" NAME="NameFilter">$Name = "Aaliya Bano -212236DP001"</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

headers = {"Content-Type": "text/xml; charset=utf-8"}
print("Requesting Aaliya Bano ledger collection from Tally...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=10)
    response.raise_for_status()
    print("Retrieved XML. Content length:", len(response.text))
    
    # Save to scratch
    with open("scratch/single_ledger_collection.xml", "w", encoding="utf-8") as f:
        f.write(response.text)
        
    # Check if there is IMDATEOFLEAVE or DATEOFLEAVING in the response
    if "DATEOFLEAVING" in response.text or "IMDATEOFLEAVE" in response.text or "CLASSOFLEAVING" in response.text:
        print("\nSUCCESS: Found leaving UDFs!")
        # Print matching lines
        for line in response.text.splitlines():
            if any(x in line for x in ("DATEOFLEAVING", "IMDATEOFLEAVE", "CLASSOFLEAVING")):
                print("  ", line.strip())
    else:
        print("\nCould not find any leaving UDFs in this response. Full XML printed below:")
        print(response.text[:2000])
except Exception as e:
    print(f"Error: {e}")
