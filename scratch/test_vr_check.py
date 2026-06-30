import requests
import xml.etree.ElementTree as ET
import re

def check_voucher_register():
    url = "http://192.168.64.2:9000"
    payload = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Voucher Register</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVFROMDATE>20250401</SVFROMDATE>
          <SVTODATE>20250401</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""

    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=60)
        content_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', response.text)
        
        with open("scratch/voucher_register_out.xml", "w", encoding="utf-8") as f:
            f.write(content_clean)
            
        root = ET.fromstring(content_clean.strip().encode('utf-8'))
        vouchers = root.findall(".//VOUCHER")
        print(f"Total Vouchers found: {len(vouchers)}")
        
        if len(vouchers) > 0:
            vch = vouchers[0]
            vch_num = vch.find("VOUCHERNUMBER")
            vch_type = vch.find("VOUCHERTYPENAME")
            print(f"First Voucher: Num={vch_num.text if vch_num is not None else 'None'}, Type={vch_type.text if vch_type is not None else 'None'}")
            
            # check for allocations
            allocs = vch.findall(".//ALLLEDGERENTRIES.LIST")
            print(f"Ledger Entries in first voucher: {len(allocs)}")
            for a in allocs[:2]:
                led = a.find("LEDGERNAME")
                print(f" - {led.text if led is not None else 'None'}")
                
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_voucher_register()
