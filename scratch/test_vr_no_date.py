import requests
import xml.etree.ElementTree as ET
import time

def fetch_voucher_register_no_date():
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
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""

    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        start = time.time()
        response = requests.post(url, data=payload, headers=headers, timeout=60)
        end = time.time()
        print("Status Code:", response.status_code)
        print("Response Length:", len(response.text))
        print(f"Time Taken: {end - start:.2f} seconds")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fetch_voucher_register_no_date()
