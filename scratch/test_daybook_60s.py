import requests
import xml.etree.ElementTree as ET
import time

def fetch_daybook():
    url = "http://192.168.64.2:9000"
    payload = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Day Book</REPORTNAME>
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
        print("Fetching Day Book with 60s timeout...")
        start_time = time.time()
        response = requests.post(url, data=payload, headers=headers, timeout=60)
        end_time = time.time()
        print(f"Status Code: {response.status_code}")
        print(f"Time Taken: {end_time - start_time:.2f} seconds")
        print("Response Length:", len(response.text))
        print("First 500 chars:", response.text[:500])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fetch_daybook()
