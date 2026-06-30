import requests

TALLY_URL = "http://103.107.67.58:9631/"

def test_extract_student_detail(company_name):
    payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>DATA</TYPE>
  <ID>StudentDetail</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
    try:
        print(f"Querying StudentDetail for company: '{company_name}'...")
        r = requests.post(TALLY_URL, data=payload, headers={"Content-Type": "text/xml"}, timeout=60)
        print("Status code:", r.status_code)
        print("Response length:", len(r.text))
        print("First 1000 chars of response:")
        print(r.text[:1000])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_extract_student_detail("SHOOLINI UNIVERSITY SOLAN (DISTANCE EDUCATION)")
