import requests
import xml.etree.ElementTree as ET
from sync_agent.config import settings

def test_tally_company_query():
    # We will try a few different XML formats to see what fields Tally returns for Company objects.
    payload = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>EXPORT</TALLYREQUEST>
    <TYPE>COLLECTION</TYPE>
    <ID>CompanyCollection</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <USERTDL>
          <COLLECTION NAME="CompanyCollection">
            <TYPE>Company</TYPE>
            <FETCH>NAME, COMPANYNUMBER, GUID, STARTINGFROM, BOOKSFROM, *</FETCH>
          </COLLECTION>
        </USERTDL>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
    
    url = settings.TALLY_URL
    print(f"Sending request to Tally URL: {url}")
    try:
        response = requests.post(url, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=15)
        print(f"Status Code: {response.status_code}")
        print("Response Content:")
        print(response.text[:2000])
    except Exception as e:
        print("Error connecting to Tally:", e)

if __name__ == "__main__":
    test_tally_company_query()
