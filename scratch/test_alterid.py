import requests
import xml.etree.ElementTree as ET

def fetch_by_alterid():
    url = "http://192.168.64.2:9000"
    payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>ModifiedVouchers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="ModifiedVouchers">
     <TYPE>Voucher</TYPE>
     <FETCH>GUID, VOUCHERNUMBER, VOUCHERTYPENAME, PARTYLEDGERNAME, DATE, ALTERID, ALLLEDGERENTRIES.LIST</FETCH>
     <!-- Only fetch vouchers with ALTERID greater than 0 to see if it's fast -->
     <FILTER>AlterIdFilter</FILTER>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="AlterIdFilter">
      $AlterID > 0
    </SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=20)
        print("Status Code:", response.status_code)
        print("Response Length:", len(response.text))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fetch_by_alterid()
