import requests
from sync_agent.config import settings

def test():
    # We use correct TDL casing: <Collection Name="...">, <Type>, <Fetch>
    payload = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>EXPORT</TALLYREQUEST>
    <TYPE>COLLECTION</TYPE>
    <ID>CustomActiveCompanies</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <TDL>
        <USERTDL>
          <Collection Name="CustomActiveCompanies">
            <Type>Company</Type>
            <Fetch>Name, CompanyNumber, CompanyCode, Token, KGCompanyCode, KGToken, KGOwnBankName</Fetch>
          </Collection>
        </USERTDL>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
    response = requests.post(settings.TALLY_URL, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=15)
    print("Response Status:", response.status_code)
    print("Response Content:")
    print(response.text)

if __name__ == "__main__":
    test()
