import requests
import re

payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>List of Groups</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="List of Groups">
     <TYPE>Group</TYPE>
     <FETCH>Name</FETCH>
     <FETCH>Parent</FETCH>
    </TDLUSERLIST>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""

headers = {"Content-Type": "text/xml; charset=utf-8"}
print("Requesting all Groups from Tally...")
try:
    response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    print("Retrieved response successfully.")
    
    xml_data = response.text
    
    # Save the raw response to scratch
    with open("scratch/tally_groups_raw.xml", "w", encoding="utf-8") as f:
        f.write(xml_data)
    print("Saved raw XML to scratch/tally_groups_raw.xml")
    
    # Regex parser for robust extraction
    # We find all <GROUP NAME="..."> ... </GROUP> blocks
    group_blocks = re.findall(r'<GROUP\s+NAME="([^"]+)"[^>]*>(.*?)</GROUP>', xml_data, re.DOTALL)
    
    groups = []
    for name, inner_content in group_blocks:
        parent_match = re.search(r'<PARENT>(.*?)</PARENT>', inner_content, re.DOTALL)
        parent = parent_match.group(1).strip() if parent_match else ""
        # Clean entities if any
        parent = re.sub(r'&#\d+;', '', parent).strip()
        name = re.sub(r'&#\d+;', '', name).strip()
        groups.append((name, parent))
        
    print(f"\nSuccessfully parsed {len(groups)} Groups using Regex:")
    for idx, (name, parent) in enumerate(sorted(groups)):
        print(f"  {idx+1}. Group: {name} (Parent: {parent})")
        
    # Save the output to a text file
    with open("scratch/tally_groups_list.txt", "w", encoding="utf-8") as f:
        f.write(f"Total Groups: {len(groups)}\n\n")
        for idx, (name, parent) in enumerate(sorted(groups)):
            f.write(f"{idx+1}. Group: {name} | Parent: {parent}\n")
    print("\nSaved full list to scratch/tally_groups_list.txt")
    
except Exception as e:
    print(f"Error: {e}")
