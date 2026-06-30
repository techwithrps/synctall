import requests
import re

TALLY_URL = "http://192.168.64.2:9000"

def check_tally():
    payload = """<ENVELOPE>
        <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
        <BODY>
            <EXPORTDATA>
                <REQUESTDESC>
                    <REPORTNAME>Voucher Register</REPORTNAME>
                    <STATICVARIABLES>
                        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                </REQUESTDESC>
            </EXPORTDATA>
        </BODY>
    </ENVELOPE>"""
    try:
        response = requests.post(TALLY_URL, data=payload, headers={'Content-Type': 'text/xml'})
        if response.status_code == 200:
            content = response.text
            vouchers = re.findall(r'<VOUCHER[^>]*>(.*?)</VOUCHER>', content, re.DOTALL)
            print(f"Total Vouchers found: {len(vouchers)}")
            
            # Count duplicates by VOUCHERNUMBER
            vch_numbers = re.findall(r'<VOUCHERNUMBER>(.*?)</VOUCHERNUMBER>', content)
            guids = re.findall(r'<GUID>(.*?)</GUID>', content)
            
            # Print some sample GUIDs
            print("Sample GUIDs in Tally:")
            for g in guids[:10]:
                print(g)
                
            from collections import Counter
            counts = Counter(vch_numbers)
            duplicates = {k: v for k, v in counts.items() if v > 1}
            print(f"Duplicate Voucher Numbers: {len(duplicates)}")
            for k, v in list(duplicates.items())[:10]:
                print(f"VchNo: {k} -> Count: {v}")
                
        else:
            print("Failed", response.status_code)
    except Exception as e:
        print("Error", e)

if __name__ == "__main__":
    check_tally()
