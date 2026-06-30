import oracledb
import requests
import xml.etree.ElementTree as ET
import re

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"
enrollment_no = "GF/2021/8052"
expected_ledger = "Atal Lingfa -GF/2021/8052"
tally_url = "http://192.168.64.2:9000"

def fetch_oracle_data():
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM C##COLLAGETEST.STUDENT_MASTER_DATA 
        WHERE ENRL_NO = :enrl_no
    """, {"enrl_no": enrollment_no})
    row = cursor.fetchone()
    if not row:
        cursor.close()
        connection.close()
        return None
    col_names = [col[0].upper() for col in cursor.description]
    data = dict(zip(col_names, row))
    cursor.close()
    connection.close()
    return data

def fetch_tally_data(name):
    payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>DATA</TYPE>
  <ID>Ledger</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVOBJECTNAME>{name}</SVOBJECTNAME>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    try:
        response = requests.post(tally_url, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error calling Tally for '{name}': {e}")
        return None

def parse_tally_xml(xml_content):
    if not xml_content or "<PARENT>" not in xml_content:
        return None
        
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_content)
    xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
    root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    
    ledger = root.find(".//LEDGER")
    if ledger is None:
        return None
        
    tally_data = {}
    
    # Simple tags
    tally_data["LEDGER_NAME"] = ledger.get("NAME")
    parent_elem = ledger.find("PARENT")
    tally_data["PARENT"] = parent_elem.text.strip() if parent_elem is not None and parent_elem.text else None
    
    # Address
    address_elem = ledger.find(".//ADDRESS.LIST")
    if address_elem is not None:
        tally_data["ADDRESS"] = ", ".join([addr.text.strip() for addr in address_elem.findall("ADDRESS") if addr.text])
        
    # UDFs
    udf_mapping = {
        "FATHER_NAME": "IMFTHNAME",
        "MOTHER_NAME": "IMMTHNAME",
        "RELIGION": "IMSTDRELIGION",
        "GENDER": "SEX",
        "ROLL_NO": "IMROLLNO",
        "COURSE": "IMCOURSE",
        "SESSION": "IMSESSION",
        "YEAR": "IMYEAR",
        "MOBILE": "CORSMOBILENO",
        "CASTE": "IMSTDCASTE",
        "CATEGORY": "STDCATEGORY",
        "REGISTRATION_NO": "IMREGTNO",
        "DOB": "MDOB",
        "ADMISSION_CATEGORY": "ADMCATEGORY",
        "RANK": "IMSTDRANK",
        "ANNUAL_INCOME": "ANNUALINCOMEOFPARENT",
        "PERMANENT_PIN": "PERMTPINCODE",
        "CORRESPONDENCE_PIN": "CORSPINCODE",
        "PERMANENT_ADDRESS": "OFFICEADDRESS",
        "QUOTA": "QUOTALED",
        "STATUS": "IMSTDSTATUS",
    }
    
    for key, udf_name in udf_mapping.items():
        udf_list = ledger.find(f".//UDF:{udf_name}.LIST")
        if udf_list is not None:
            udf_val = udf_list.find(f"UDF:{udf_name}")
            if udf_val is not None and udf_val.text:
                tally_data[key] = udf_val.text.strip()
                
    return tally_data

def compare():
    oracle = fetch_oracle_data()
    if not oracle:
        print("Oracle record not found!")
        return
        
    # Let's try to query by primary ledger name first
    print(f"Trying to fetch primary ledger: {expected_ledger}")
    tally_xml = fetch_tally_data(expected_ledger)
    tally = parse_tally_xml(tally_xml)
    
    if not tally:
        # Fallback to alias
        print(f"Primary not found. Trying to fetch alias: {enrollment_no}")
        tally_xml = fetch_tally_data(enrollment_no)
        tally = parse_tally_xml(tally_xml)
        
    if not tally:
        print("Ledger not found in Tally! The student does not exist in Tally.")
        if tally_xml:
            print("Raw Tally XML:")
            print(tally_xml[:1000])
        return
        
    # Print comparison
    print(f"\nComparing data for: {enrollment_no}")
    print(f"{'Field':<25} | {'Oracle DB Value':<40} | {'Tally Value':<40}")
    print("-" * 110)
    
    comparisons = [
        ("Student Name", oracle.get("STUDENT_NAME"), tally.get("LEDGER_NAME")),
        ("Parent Group/Class", oracle.get("BRANCH"), tally.get("PARENT")),
        ("Mobile", oracle.get("STUDENT_MOBILE"), tally.get("MOBILE")),
        ("Father Name", oracle.get("FATHER_NAME"), tally.get("FATHER_NAME")),
        ("Mother Name", oracle.get("MOTHER_NAME"), tally.get("MOTHER_NAME")),
        ("Course", oracle.get("COURSE"), tally.get("COURSE")),
        ("Session", oracle.get("SESSION_YEAR"), tally.get("SESSION")),
        ("Roll No", oracle.get("ROLL_NO"), tally.get("ROLL_NO")),
        ("Reg No", oracle.get("REG_NO"), tally.get("REG_NO")),
        ("Gender", oracle.get("STUDENT_GENDER"), tally.get("GENDER")),
        ("Current Address", oracle.get("CURRENT_ADDRESS"), tally.get("ADDRESS")),
        ("Permanent Address", oracle.get("PERMANENT_ADDRESS"), tally.get("PERMANENT_ADDRESS")),
    ]
    
    diffs = 0
    for label, db_val, tally_val in comparisons:
        db_clean = str(db_val or "").strip()
        tally_clean = str(tally_val or "").strip()
        
        # Strip suffix from Tally name for comparison
        if label == "Student Name" and tally_clean.endswith(f"-{enrollment_no}"):
            tally_clean = tally_clean.replace(f"-{enrollment_no}", "").strip()
            
        # Clean address newline/spacing variations for fair comparison
        if "Address" in label:
            db_clean = re.sub(r'\s+', ' ', db_clean)
            tally_clean = re.sub(r'\s+', ' ', tally_clean)
            
        is_diff = db_clean.lower() != tally_clean.lower()
        marker = "!!!" if is_diff else "   "
        if is_diff:
            diffs += 1
            
        print(f"{marker} {label:<21} | {db_clean:<40} | {tally_clean:<40}")
        
    print("-" * 110)
    print(f"Comparison completed. Found {diffs} difference(s).")
    
compare()
