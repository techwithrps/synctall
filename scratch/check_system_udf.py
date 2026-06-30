import requests
from sync_agent.config import settings

def test():
    payload = """<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>EXPORT</TALLYREQUEST>
    <TYPE>COLLECTION</TYPE>
    <ID>UDF</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      </STATICVARIABLES>
      <FETCHLIST>
        <FETCH>NAME</FETCH>
      </FETCHLIST>
    </DESC>
  </BODY>
</ENVELOPE>"""
    response = requests.post(settings.TALLY_URL, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=15)
    print("Response Status:", response.status_code)
    print("Response:")
    content = response.text
    print(content[:2000])
    
    # Filter UDFs containing "code", "token", "elogipay", "company"
    print("\nFiltering UDFs...")
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(content)
        for udf in root.findall(".//UDF"):
            name_elem = udf.find("NAME")
            if name_elem is not None and name_elem.text:
                name = name_elem.text.strip()
                if any(term in name.lower() for term in ["code", "token", "elogipay", "company", "bank"]):
                    print("Found UDF Name:", name)
    except Exception as e:
        print("Parse error:", e)

if __name__ == "__main__":
    test()
