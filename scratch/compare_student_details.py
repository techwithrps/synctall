import oracledb
import xml.etree.ElementTree as ET
import re

user = "C##COLLEGETEST"
password = "COLLEGETEST_1250#"
dsn = "103.234.185.186:1521/xe"
enrollment_no = "GF/2021/8052"

def fetch_oracle_data():
    try:
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
    except Exception as e:
        print("Oracle Error:", e)
        return None

def parse_tally_details():
    try:
        import requests
        payload = """<ENVELOPE>
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
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
        headers = {"Content-Type": "text/xml; charset=utf-8"}
        response = requests.post("http://192.168.64.2:9000", data=payload, headers=headers, timeout=20)
        response.raise_for_status()
        content = response.text
        
        # Clean control characters
        xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
        xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
        
        from sync_agent.parser import parse_students_xml
        students = parse_students_xml(content)
        
        for student in students:
            if student.get("enrollment_no") == enrollment_no:
                return student
        return None
    except Exception as e:
        print("Tally parse error:", e)
        return None

def main():
    oracle = fetch_oracle_data()
    tally = parse_tally_details()
    
    if not oracle:
        print(f"Oracle data not found for student {enrollment_no}!")
        return
    if not tally:
        print(f"Tally student details not found for student {enrollment_no} in XML!")
        return
        
    print(f"\n=======================================================================")
    print(f"SIDE-BY-SIDE DIFF FOR STUDENT: {enrollment_no}")
    print(f"=======================================================================")
    print(f"{'Field / Description':<25} | {'Oracle DB Value':<32} | {'Tally Value':<32} | {'Status':<10}")
    print("-" * 110)
    
    # We will define the mappings to compare:
    comparisons = [
        ("Student Name", oracle.get("STUDENT_NAME"), tally.get("student_name")),
        ("Gender", oracle.get("STUDENT_GENDER"), tally.get("gender")),
        ("Mobile", oracle.get("STUDENT_MOBILE"), tally.get("mobile") or tally.get("raw_payload", {}).get("KGCRSMOB")),
        ("Email ID", oracle.get("STUDENT_EMAIL_ID"), tally.get("email")),
        ("Father Name", oracle.get("FATHER_NAME"), tally.get("father_name")),
        ("Course", oracle.get("COURSE"), tally.get("course")),
        ("Class/Branch", oracle.get("BRANCH"), tally.get("student_class")),
        ("Session Year", oracle.get("SESSION_YEAR"), tally.get("session")),
        ("Current Address", oracle.get("CURRENT_ADDRESS"), tally.get("correspondence_address") or tally.get("permanent_address")),
    ]
    
    diff_count = 0
    for label, db_val, tally_val in comparisons:
        db_str = str(db_val or "").strip()
        tally_str = str(tally_val or "").strip()
        
        # Format address nicely for comparison
        if "Address" in label:
            db_str_comp = re.sub(r'\s+', ' ', db_str).lower().strip()
            tally_str_comp = re.sub(r'\s+', ' ', tally_str).lower().strip()
            # If Tally's value is truncated but is a prefix of DB value, consider it a match
            if tally_str_comp and db_str_comp.startswith(tally_str_comp):
                db_str_comp = tally_str_comp
        elif label == "Class/Branch":
            from sync_agent.tally_client import clean_group_name
            db_str_comp = clean_group_name(db_str).lower().strip()
            tally_str_comp = clean_group_name(tally_str).lower().strip()
        elif label == "Student Name":
            # Strip enrollment number suffix
            db_str_comp = db_str.lower().strip()
            tally_str_comp = tally_str.lower().strip()
            suffix = f"-{enrollment_no}".lower()
            if tally_str_comp.endswith(suffix):
                tally_str_comp = tally_str_comp[:-len(suffix)].strip()
        else:
            db_str_comp = db_str.lower().strip()
            tally_str_comp = tally_str.lower().strip()
            
        if db_str_comp == tally_str_comp:
            status = "MATCH"
        else:
            status = "MISMATCH"
            diff_count += 1
            
        print(f"{label:<25} | {db_str[:32]:<32} | {tally_str[:32]:<32} | {status:<10}")
        if len(db_str) > 32 or len(tally_str) > 32:
            print(f"{'':<25} | {db_str[32:64]:<32} | {tally_str[32:64]:<32} |")
            if len(db_str) > 64 or len(tally_str) > 64:
                print(f"{'':<25} | {db_str[64:96]:<32} | {tally_str[64:96]:<32} |")
                
    print("-" * 110)
    print(f"Total differences found: {diff_count}")
    print(f"=======================================================================")

if __name__ == "__main__":
    main()
