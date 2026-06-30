import requests
import xml.etree.ElementTree as ET
import time

def fetch_with_long_timeout():
    url = "http://192.168.64.2:9000"
    payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>AprilVouchers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="AprilVouchers">
     <TYPE>Voucher</TYPE>
     <FILTER>IsAprilFirst</FILTER>
     <FETCH>GUID, VOUCHERNUMBER, VOUCHERTYPENAME, PARTYLEDGERNAME, AMOUNT</FETCH>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="IsAprilFirst">$$Date = '20250401'</SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        print("Sending request to Tally with 120s timeout...")
        start_time = time.time()
        response = requests.post(url, data=payload, headers=headers, timeout=120)
        end_time = time.time()
        print(f"Status Code: {response.status_code}")
        print(f"Time Taken: {end_time - start_time:.2f} seconds")
        print(f"Response Length: {len(response.text)}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fetch_with_long_timeout()
