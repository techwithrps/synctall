import requests

payload = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Companies</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""

url = "http://103.107.67.50:9001/"
try:
    response = requests.post(url, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=15)
    print("Response Status:", response.status_code)
    print("Response Body:\n", response.text)
except Exception as e:
    print("Error querying Tally:", e)
