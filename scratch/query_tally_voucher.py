import requests
import xml.etree.ElementTree as ET
import re

def query_vouchers():
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
     <FETCH>GUID, VOUCHERNUMBER, VOUCHERTYPENAME, PARTYLEDGERNAME, AMOUNT</FETCH>
    </TDLUSERLIST>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        content = response.text
        
        # Clean XML
        content_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
        root = ET.fromstring(content_clean.strip().encode('utf-8'))
        
        vouchers = root.findall(".//VOUCHER")
        print(f"Total Vouchers found in Tally: {len(vouchers)}")
        for vch in vouchers:
            vch_type = vch.find("VOUCHERTYPENAME")
            vch_type_str = vch_type.text.strip() if vch_type is not None else ""
            if vch_type_str != "Due Fee":
                continue
                
            guid = vch.find("GUID")
            vch_num = vch.find("VOUCHERNUMBER")
            party = vch.find("PARTYLEDGERNAME")
            
            # Get ledger entries to find amount
            ledgers = vch.findall(".//ALLLEDGERENTRIES.LIST")
            amount_str = "0.0"
            for led in ledgers:
                led_name = led.find("LEDGERNAME")
                if led_name is not None and led_name.text and "Test Kid" in led_name.text:
                    amt = led.find("AMOUNT")
                    if amt is not None:
                        amount_str = amt.text
            
            print(f"Voucher Number: {vch_num.text if vch_num is not None else 'None'}")
            print(f"  GUID: {guid.text if guid is not None else 'None'}")
            print(f"  Party: {party.text if party is not None else 'None'}")
            print(f"  Amount: {amount_str}")
            print("-" * 50)
            
    except Exception as e:
        print("Error querying vouchers from Tally:", e)

if __name__ == "__main__":
    query_vouchers()
