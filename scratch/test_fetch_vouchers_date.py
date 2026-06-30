import requests
import xml.etree.ElementTree as ET
import re

def query_tally_vouchers_by_date():
    url = "http://192.168.64.2:9000"
    payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>List of Vouchers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="List of Vouchers">
     <TYPE>Voucher</TYPE>
     <FETCH>GUID, VOUCHERNUMBER, VOUCHERTYPENAME, PARTYLEDGERNAME, DATE, ALLLEDGERENTRIES.LIST</FETCH>
     <FILTER>DateFilter</FILTER>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="DateFilter">
      $DATE = $$Date:"1-Apr-25"
    </SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=60)
        content = response.text
        content_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
        root = ET.fromstring(content_clean.strip().encode('utf-8'))
        
        vouchers = root.findall(".//VOUCHER")
        print(f"Total Vouchers on 1-Apr-25: {len(vouchers)}")
                
    except Exception as e:
        print("Error querying vouchers from Tally:", e)

if __name__ == "__main__":
    query_tally_vouchers_by_date()
