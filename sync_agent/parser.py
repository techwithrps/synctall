import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from .logger import setup_logger
from .config import settings

logger = setup_logger("parser", settings.LOG_LEVEL)

# Mapping of Tally XML fields (all uppercase for case-insensitive lookup) to DB columns
FIELD_MAPPING = {
    "KGENRNO": "enrollment_no",
    "KGSTUDNAME": "student_name",
    "KGSTUDCLASS": "student_class",
    "KGROLLNO": "roll_no",
    "KGREGTNO": "registration_no",
    "KGCOURSE": "course",
    "KGSEMESTER": "semester",
    "KGSESSION": "session",
    "KGYEAR": "year",
    "KGFATHERNAME": "father_name",
    "KGMOTHERNAME": "mother_name",
    "KGQUOTA": "quota",
    "KGSEX": "gender",
    "KGDOB": "dob",
    "KGBLDGRP": "blood_group",
    "KGMOBNO": "mobile",
    "KGCRSMOB": "mobile",
    "KGCATEGRY": "category",
    "KGSUBCATEGRY": "subcategory",
    "KGEMAL": "email",
    "KGBILLWISE": "billwise",
    "KGADMCTG": "admission_category",
    "KGSEERNO": "seer_no",
    "KGRANK": "rank",
    "KGRLGN": "religion",
    "KGCASTE": "caste",
    "KGANLINCOME": "annual_income",
    "KGSTATUS": "status",
    "KGSUBSTATUS": "substatus",
    "KGOPENING": "opening_balance",
    "KGCLOSING": "closing_balance",
    "KGPRMTADD": "permanent_address",
    "KGPIN": "permanent_pin",
    "KGCRSPDADDR": "correspondence_address",
    "KGCRSPIN": "correspondence_pin",
    "KGSTDCREATEBY": "created_by",
    "KGSTDCREATETIME": "created_time",
    "KGREMARK": "remarks",
    "KGADMMODE": "admission_mode"
}

def parse_tally_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str or not date_str.strip() or date_str.strip() == "Not Applicable":
        return None
        
    date_str = date_str.strip()
    
    if re.match(r'^\d{8}$', date_str):
        try:
            return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except Exception:
            pass
            
    for fmt in ('%d-%b-%y', '%d-%b-%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            parsed_dt = datetime.strptime(date_str, fmt)
            return parsed_dt.date().isoformat()
        except ValueError:
            continue
            
    cleaned = re.sub(r'[^\d\-]', '', date_str)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', cleaned):
        return cleaned
        
    return None

def parse_tally_datetime(dt_str: Optional[str]) -> Optional[str]:
    if not dt_str or not dt_str.strip():
        return None
    dt_str = dt_str.strip()
    
    if ' at ' in dt_str:
        dt_str = dt_str.replace(' at ', ' ')
        parts = dt_str.split(' ')
        if len(parts) > 1 and len(parts[1].split(':')) == 2:
            dt_str = f"{parts[0]} {parts[1]}:00"
    
    formats = [
        '%Y%m%d%H%M%S',
        '%d-%b-%y %H:%M:%S',
        '%d-%b-%Y %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S'
    ]
    for fmt in formats:
        try:
            parsed_dt = datetime.strptime(dt_str, fmt)
            return parsed_dt.isoformat()
        except ValueError:
            continue
            
    return None

def parse_numeric(val: Optional[str]) -> float:
    if not val or not val.strip():
        return 0.0
    val_clean = val.strip().replace(",", "")
    try:
        return float(val_clean)
    except ValueError:
        return 0.0

def parse_boolean(val: Optional[str]) -> bool:
    if not val:
        return False
    val_lower = val.strip().lower()
    return val_lower in ('yes', 'true', '1')

def parse_students_xml(xml_content: str) -> List[Dict[str, Any]]:
    """
    Cleans raw XML and uses a sequential flat-stream algorithm. 
    This guarantees capturing all records regardless of how Tally nests or flattens the XML hierarchy.
    """
    if not xml_content or not xml_content.strip():
        return []

    # Strip invalid control characters
    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_content)
    
    try:
        root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    except Exception as e:
        logger.error(f"XML Parsing crashed: {str(e)}")
        return []
        
    students = []
    current_student = {}
    current_raw = {}
    
    # Traverse entire DOM tree in sequential depth-first order
    for elem in root.iter():
        tag_upper = elem.tag.upper()
        
        if tag_upper in FIELD_MAPPING:
            db_col = FIELD_MAPPING[tag_upper]
            val = elem.text.strip() if elem.text else ""
            
            # Boundary trigger: if we hit a primary key field that we ALREADY have 
            # in the current accumulator, it means we've transitioned to the NEXT student record!
            if (db_col == "enrollment_no" and "enrollment_no" in current_student) or \
               (db_col == "student_name" and "student_name" in current_student):
                
                # Flush and save the completed student record
                if "enrollment_no" in current_student:
                    if not current_student.get("student_name"):
                        current_student["student_name"] = "Unknown Student"
                    current_student["raw_payload"] = current_raw
                    students.append(current_student)
                
                # Reset accumulators for the new student
                current_student = {}
                current_raw = {}
                
            # Accumulate fields
            current_raw[elem.tag] = val
            
            if db_col == "dob":
                current_student[db_col] = parse_tally_date(val)
            elif db_col == "created_time":
                current_student[db_col] = parse_tally_datetime(val)
            elif db_col in ("opening_balance", "closing_balance"):
                # Tally stores Debit balances as negative numbers and Credit balances as positive numbers in XML.
                # For student accounts (receivables), a Debit balance is an asset (money owed to college),
                # which should be represented as a positive number in the DB, and a Credit balance (advance payment)
                # should be represented as a negative number. Hence we invert the sign.
                current_student[db_col] = -parse_numeric(val)
            elif db_col == "annual_income":
                current_student[db_col] = parse_numeric(val)
            elif db_col == "billwise":
                current_student[db_col] = parse_boolean(val)
            else:
                current_student[db_col] = val

    # Don't forget to flush the last accumulated student at the end of the document
    if current_student and "enrollment_no" in current_student:
        if not current_student.get("student_name"):
            current_student["student_name"] = "Unknown Student"
        current_student["raw_payload"] = current_raw
        students.append(current_student)
                
    logger.info(f"Parsed {len(students)} student records from XML DOM tree.")
    return students

def clean_el(elem: ET.Element) -> Any:
    if len(elem) == 0:
        return elem.text.strip() if elem.text else ""
    res = {}
    for child in elem:
        # remove namespace prefix to keep JSON payload clean
        tag_clean = child.tag.split('}')[-1].split(':')[-1]
        val = clean_el(child)
        if val != "":
            if tag_clean in res:
                if not isinstance(res[tag_clean], list):
                    res[tag_clean] = [res[tag_clean]]
                res[tag_clean].append(val)
            else:
                res[tag_clean] = val
    return res

def extract_enrollment_no(party_ledger_name: str) -> Optional[str]:
    if not party_ledger_name:
        return None
    party_ledger_name = party_ledger_name.strip()
    if '-' in party_ledger_name:
        parts = party_ledger_name.rsplit('-', 1)
        return parts[1].strip()
    return party_ledger_name

def get_udf_value(parent_el: ET.Element, udf_base_name: str) -> Optional[str]:
    for child in parent_el:
        tag_clean = child.tag
        if '}' in tag_clean:
            tag_clean = tag_clean.split('}', 1)[1]
        elif ':' in tag_clean:
            tag_clean = tag_clean.split(':', 1)[1]
        
        if tag_clean == f"{udf_base_name}.LIST":
            inner_el = child.find(f"./{{TallyUDF}}{udf_base_name}")
            if inner_el is None:
                inner_el = child.find(f"./UDF:{udf_base_name}")
            if inner_el is None:
                for sub in child:
                    sub_tag = sub.tag.split('}')[-1].split(':')[-1]
                    if sub_tag == udf_base_name:
                        return sub.text.strip() if sub.text else None
            else:
                return inner_el.text.strip() if inner_el.text else None
    return None

def parse_transactions_xml(xml_content: str) -> List[Dict[str, Any]]:
    if not xml_content or not xml_content.strip():
        return []

    xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_content)
    xml_clean = xml_clean.replace('</UDF:VCHBILLSEMNAME.LIST\n', '</UDF:VCHBILLSEMNAME.LIST>\n')
    xml_clean = xml_clean.replace('</UDF:VCHBILLSEMNAME.LIST\r\n', '</UDF:VCHBILLSEMNAME.LIST>\r\n')

    def repl(match):
        val_str = match.group(1)
        if val_str.startswith('x') or val_str.startswith('X'):
            val = int(val_str[1:], 16)
        else:
            val = int(val_str)
        if val < 32 and val not in (9, 10, 13):
            return ""
        return match.group(0)
    xml_clean = re.sub(r'&#(x?[0-9a-fA-F]+);', repl, xml_clean)

    try:
        root = ET.fromstring(xml_clean.strip().encode('utf-8'))
    except Exception as e:
        logger.error(f"Transactions XML Parsing crashed: {str(e)}")
        return []

    transactions = []
    vouchers = root.findall('.//VOUCHER')
    
    for vch in vouchers:
        vch_type_el = vch.find('VOUCHERTYPENAME')
        vch_type = vch_type_el.text.strip() if vch_type_el is not None and vch_type_el.text else ""
        
        if vch_type not in ('Due Fee', 'Fees Receipt', 'Receipt', 'Journal'):
            continue
            
        guid_el = vch.find('GUID')
        guid = guid_el.text.strip() if guid_el is not None and guid_el.text else None
        if not guid:
            continue
            
        date_el = vch.find('DATE')
        date_raw = date_el.text.strip() if date_el is not None and date_el.text else None
        date_val = parse_tally_date(date_raw)
        
        vch_num_el = vch.find('VOUCHERNUMBER')
        vch_num = vch_num_el.text.strip() if vch_num_el is not None and vch_num_el.text else ""
        
        party_ledger_el = vch.find('PARTYLEDGERNAME')
        party_ledger = party_ledger_el.text.strip() if party_ledger_el is not None and party_ledger_el.text else ""
        
        enrollment_no = extract_enrollment_no(party_ledger)
        
        student_entry = None
        ledger_entries = vch.findall('.//ALLLEDGERENTRIES.LIST')
        for entry in ledger_entries:
            led_name_el = entry.find('LEDGERNAME')
            led_name = led_name_el.text.strip() if led_name_el is not None and led_name_el.text else ""
            if led_name == party_ledger:
                student_entry = entry
                break
                
        if student_entry is None:
            for entry in ledger_entries:
                led_name_el = entry.find('LEDGERNAME')
                led_name = led_name_el.text.strip() if led_name_el is not None and led_name_el.text else ""
                is_party_el = entry.find('ISPARTYLEDGER')
                is_party = is_party_el.text.strip().lower() if is_party_el is not None and is_party_el.text else ""
                if is_party == 'yes' and enrollment_no and enrollment_no in led_name:
                    student_entry = entry
                    break

        if student_entry is None:
            continue
            
        # Determine opposite ledger name as particulars
        particulars = vch_type
        for entry in ledger_entries:
            led_name_el = entry.find('LEDGERNAME')
            led_name = led_name_el.text.strip() if led_name_el is not None and led_name_el.text else ""
            if led_name and led_name != party_ledger:
                particulars = led_name
                break

        amount_el = student_entry.find('AMOUNT')
        amount_raw = amount_el.text.strip() if amount_el is not None and amount_el.text else "0.0"
        amount = parse_numeric(amount_raw)
        
        allocations = []
        bill_allocs = student_entry.findall('.//BILLALLOCATIONS.LIST')
        for alloc in bill_allocs:
            name_el = alloc.find('NAME')
            name = name_el.text.strip() if name_el is not None and name_el.text else ""
            
            bill_type_el = alloc.find('BILLTYPE')
            bill_type = bill_type_el.text.strip() if bill_type_el is not None and bill_type_el.text else ""
            
            alloc_amount_el = alloc.find('AMOUNT')
            alloc_amount_raw = alloc_amount_el.text.strip() if alloc_amount_el is not None and alloc_amount_el.text else "0.0"
            alloc_amount = parse_numeric(alloc_amount_raw)
            
            fee_head = get_udf_value(alloc, 'VCHBILLFEENAME')
            semester = get_udf_value(alloc, 'VCHBILLSEMNAME')
            
            allocations.append({
                "bill_name": name,
                "bill_type": bill_type,
                "amount": alloc_amount,
                "fee_head": fee_head,
                "semester": semester
            })
            
        raw_payload = clean_el(vch)
        
        transactions.append({
            "guid": guid,
            "date": date_val,
            "voucher_number": vch_num,
            "voucher_type": vch_type,
            "party_ledger_name": party_ledger,
            "particulars": particulars,
            "enrollment_no": enrollment_no,
            "amount": amount,
            "allocations": allocations,
            "raw_payload": raw_payload
        })
        
    logger.info(f"Parsed {len(transactions)} transaction records from XML.")
    return transactions
