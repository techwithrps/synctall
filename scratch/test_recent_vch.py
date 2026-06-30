import requests
import xml.etree.ElementTree as ET

def fetch_recent():
    url = "http://192.168.64.2:9000"
    payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>RecentVouchers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="RecentVouchers">
     <TYPE>Voucher</TYPE>
     <FETCH>GUID, VOUCHERNUMBER, VOUCHERTYPENAME, PARTYLEDGERNAME, DATE, ALLLEDGERENTRIES.LIST</FETCH>
     <!-- Vouchers for today or the last few days -->
     <FILTER>RecentFilter</FILTER>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="RecentFilter">
      $Date = '20250401'
    </SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        print("Status Code:", response.status_code)
        
        # Clean XML
        import re
        content_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
        root = ET.fromstring(content_clean.strip().encode('utf-8'))
        
        vouchers = root.findall(".//VOUCHER")
        print(f"Total Recent Vouchers: {len(vouchers)}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fetch_recent()
