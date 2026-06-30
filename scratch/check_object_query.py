import requests
from sync_agent.config import settings

def test():
    # We query the currently loaded company as an OBJECT, which exports all fields and UDFs.
    payload = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>EXPORT</TALLYREQUEST>
    <TYPE>OBJECT</TYPE>
    <ID>Company</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVCURRENTCOMPANY>SHOOLINI UNIVERSITY SOLAN (DISTANCE EDUCATION)</SVCURRENTCOMPANY>
      </STATICVARIABLES>
    </DESC>
  </BODY>
</ENVELOPE>"""
    response = requests.post(settings.TALLY_URL, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=15)
    print("Response Status:", response.status_code)
    print("Response Content length:", len(response.text))
    # We will print the response content. If it is huge, we will search for Code or Token in it.
    content = response.text
    print("\nFirst 1000 chars:")
    print(content[:1000])
    
    print("\nSearching for potential matches...")
    for line in content.split("\n"):
        if any(term in line.lower() for term in ["12", "shiol", "token", "code", "bank"]):
            print(line.strip())

if __name__ == "__main__":
    test()
