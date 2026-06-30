import requests
import xml.etree.ElementTree as ET

def fetch_voucher_register():
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
        print("Status Code:", response.status_code)
        print("Response Length:", len(response.text))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fetch_voucher_register()
