import requests
import xml.etree.ElementTree as ET
import re

def query_all_tally_vouchers():
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
     <FILTER>PartyFilter</FILTER>
     <FETCH>GUID, VOUCHERNUMBER, VOUCHERTYPENAME, PARTYLEDGERNAME, DATE</FETCH>
    </TDLUSERLIST>
    <SYSTEM TYPE="Formulae" NAME="PartyFilter">
      $PARTYLEDGERNAME = "Rajesh-1223 -1223" or $PARTYLEDGERNAME = "Rajesh-1223" or $PARTYLEDGERNAME = "Rajesh-1223 - 1223"
    </SYSTEM>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
    
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=30)
        content = response.text
        content_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
        root = ET.fromstring(content_clean.strip().encode('utf-8'))
        
        vouchers = root.findall(".//VOUCHER")
        print(f"Total Vouchers in Tally matching Rajesh-1223: {len(vouchers)}")
        for vch in vouchers:
            vch_num = vch.find("VOUCHERNUMBER")
            vch_num_str = vch_num.text.strip() if vch_num is not None else "None"
            
            vch_type = vch.find("VOUCHERTYPENAME")
            vch_type_str = vch_type.text.strip() if vch_type is not None else "None"
            
            party = vch.find("PARTYLEDGERNAME")
            party_str = party.text.strip() if party is not None else "None"
            
            date = vch.find("DATE")
            date_str = date.text.strip() if date is not None else "None"
            
            # Print all ledger entries inside the voucher
            ledgers = vch.findall(".//ALLLEDGERENTRIES.LIST")
            ledger_details = []
            for led in ledgers:
                lname = led.find("LEDGERNAME")
                lamt = led.find("AMOUNT")
                lname_str = lname.text.strip() if lname is not None else "None"
                lamt_str = lamt.text.strip() if lamt is not None else "0.0"
                ledger_details.append(f"{lname_str}: {lamt_str}")
                
            print(f"Vch No: {vch_num_str} | Type: {vch_type_str} | Date: {date_str} | Party: {party_str}")
            print("Ledgers:")
            for ld in ledger_details:
                print(f"  - {ld}")
            print("-" * 50)
                
    except Exception as e:
        print("Error querying vouchers from Tally:", e)

if __name__ == "__main__":
    query_all_tally_vouchers()
