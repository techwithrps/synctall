import requests
from sync_agent.config import settings

def test():
    payload = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>EXPORT</TALLYREQUEST>
    <TYPE>COLLECTION</TYPE>
    <ID>UDFCollection</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <USERTDL>
          <COLLECTION NAME="UDFCollection">
            <TYPE>UDF</TYPE>
            <FETCH>*</FETCH>
          </COLLECTION>
        </USERTDL>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
    response = requests.post(settings.TALLY_URL, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=15)
    print("Response Status:", response.status_code)
    print("Response:")
    print(response.text[:5000])

if __name__ == "__main__":
    test()
