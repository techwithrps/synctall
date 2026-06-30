import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError
import time
import re
from .config import settings
from .logger import setup_logger

logger = setup_logger("tally_client", settings.LOG_LEVEL)

def escape_xml(val) -> str:
    if val is None:
        return ""
    val_str = str(val)
    return val_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def parse_city_state(address_str: str) -> tuple:
    if not address_str or not str(address_str).strip() or str(address_str).strip().lower() in ("none", "null", "nan"):
        return None, None
    
    addr_clean = address_str.strip()
    # Remove pincode if it's at the end
    addr_clean = re.sub(r'\b\d{6}\b', '', addr_clean).strip()
    parts = [p.strip() for p in addr_clean.split(',') if p.strip()]
    
    city = None
    state = None  # No default fallback
    
    text_lower = address_str.lower()
    
    # Comprehensive state keyword matching
    states_map = {
        "bihar": "Bihar",
        "haryana": "Haryana",
        "delhi": "Delhi",
        "punjab": "Punjab",
        "uttarakhand": "Uttarakhand",
        "uk": "Uttarakhand",
        "u.k.": "Uttarakhand",
        "himachal": "Himachal Pradesh",
        "hp": "Himachal Pradesh",
        "h.p.": "Himachal Pradesh",
        "uttar pradesh": "Uttar Pradesh",
        "up": "Uttar Pradesh",
        "u.p.": "Uttar Pradesh",
        "rajasthan": "Rajasthan",
        "west bengal": "West Bengal",
        "wb": "West Bengal",
        "w.b.": "West Bengal",
        "madhya pradesh": "Madhya Pradesh",
        "mp": "Madhya Pradesh",
        "m.p.": "Madhya Pradesh",
        "jharkhand": "Jharkhand",
        "gujarat": "Gujarat",
        "maharashtra": "Maharashtra",
        "chhattisgarh": "Chhattisgarh",
        "odisha": "Odisha",
        "orissa": "Odisha",
        "karnataka": "Karnataka",
        "kerala": "Kerala",
        "tamil nadu": "Tamil Nadu",
        "telangana": "Telangana",
        "andhra pradesh": "Andhra Pradesh",
        "ap": "Andhra Pradesh",
        "a.p.": "Andhra Pradesh",
        "assam": "Assam",
        "jammu": "Jammu & Kashmir",
        "kashmir": "Jammu & Kashmir",
        "j&k": "Jammu & Kashmir",
        "goa": "Goa",
        "manipur": "Manipur",
        "meghalaya": "Meghalaya",
        "mizoram": "Mizoram",
        "nagaland": "Nagaland",
        "sikkim": "Sikkim",
        "tripura": "Tripura",
        "arunachal": "Arunachal Pradesh"
    }
    
    matched_state = None
    for key, val in states_map.items():
        if len(key) <= 3:
            # Short code, use word boundary to avoid partial matching (e.g. 'up' in 'gupta')
            if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
                matched_state = val
                break
        else:
            if key in text_lower:
                matched_state = val
                break
                
    # If no state matches, search for major cities in states
    if not matched_state:
        city_to_state_map = {
            # Bihar
            "patna": "Bihar", "gaya": "Bihar", "bhagalpur": "Bihar", "muzaffarpur": "Bihar",
            "purnia": "Bihar", "darbhanga": "Bihar", "bihar sharif": "Bihar", "arrah": "Bihar",
            "begusarai": "Bihar", "katihar": "Bihar", "munger": "Bihar", "chhapra": "Bihar",
            "danapur": "Bihar", "bettiah": "Bihar", "saharsa": "Bihar", "sasaram": "Bihar",
            "hajipur": "Bihar", "dehri": "Bihar", "siwan": "Bihar", "motihari": "Bihar",
            "nawada": "Bihar", "buxar": "Bihar", "kishanganj": "Bihar", "sitamarhi": "Bihar",
            "jamalpur": "Bihar", "jehanabad": "Bihar", "aurangabad": "Bihar", "samastipur": "Bihar",
            "zeradei": "Bihar",
            # Haryana
            "gurgaon": "Haryana", "gurugram": "Haryana", "faridabad": "Haryana", "rohtak": "Haryana",
            "panipat": "Haryana", "ambala": "Haryana", "yamunanagar": "Haryana", "hisar": "Haryana",
            "karnal": "Haryana", "sonipat": "Haryana", "panchkula": "Haryana", "kurukshetra": "Haryana",
            # Himachal Pradesh
            "shimla": "Himachal Pradesh", "solan": "Himachal Pradesh", "dharamshala": "Himachal Pradesh",
            "mandi": "Himachal Pradesh", "hamirpur": "Himachal Pradesh", "kullu": "Himachal Pradesh",
            "chamba": "Himachal Pradesh", "kangra": "Himachal Pradesh", "bilaspur": "Himachal Pradesh",
            "una": "Himachal Pradesh", "sirmaur": "Himachal Pradesh",
            # Punjab
            "ludhiana": "Punjab", "amritsar": "Punjab", "jalandhar": "Punjab", "patiala": "Punjab",
            "bathinda": "Punjab", "hoshiarpur": "Punjab", "mohali": "Punjab", "pathankot": "Punjab",
            # Uttarakhand
            "dehradun": "Uttarakhand", "haridwar": "Uttarakhand", "nainital": "Uttarakhand",
            "roorkee": "Uttarakhand", "haldwani": "Uttarakhand", "rudrapur": "Uttarakhand",
            "rishikesh": "Uttarakhand",
            # Delhi
            "delhi": "Delhi", "new delhi": "Delhi",
            # Rajasthan
            "jaipur": "Rajasthan", "jodhpur": "Rajasthan", "udaipur": "Rajasthan", "kota": "Rajasthan",
            "bikaner": "Rajasthan", "ajmer": "Rajasthan", "jhunjhunu": "Rajasthan", "alwar": "Rajasthan",
            # West Bengal
            "kolkata": "West Bengal", "howrah": "West Bengal", "durgapur": "West Bengal",
            "asansol": "West Bengal", "siliguri": "West Bengal", "jalpaiguri": "West Bengal",
            # Uttar Pradesh
            "noida": "Uttar Pradesh", "greater noida": "Uttar Pradesh", "ghaziabad": "Uttar Pradesh",
            "lucknow": "Uttar Pradesh", "kanpur": "Uttar Pradesh", "agra": "Uttar Pradesh",
            "varanasi": "Uttar Pradesh", "meerut": "Uttar Pradesh", "prayagraj": "Uttar Pradesh",
            "allahabad": "Uttar Pradesh", "bareilly": "Uttar Pradesh", "aligarh": "Uttar Pradesh",
            "moradabad": "Uttar Pradesh", "saharanpur": "Uttar Pradesh", "gorakhpur": "Uttar Pradesh",
            "jhansi": "Uttar Pradesh", "muzaffarnagar": "Uttar Pradesh", "mathura": "Uttar Pradesh",
            "ayodhya": "Uttar Pradesh", "hapur": "Uttar Pradesh", "firozabad": "Uttar Pradesh"
        }
        for city_key, state_val in city_to_state_map.items():
            if re.search(r'\b' + re.escape(city_key) + r'\b', text_lower):
                matched_state = state_val
                break
                
    if matched_state:
        state = matched_state
    
    if state == "Delhi":
        city = "Delhi"
        
    if not city and parts:
        last_part = parts[-1]
        if last_part.lower() in ("up", "u.p.", "uttar pradesh", "india", "bihar", "haryana", "delhi", "punjab", "rajasthan", "west bengal", "himachal pradesh", "hp", "h.p.") or last_part.strip() == "":
            if len(parts) > 1:
                city = parts[-2]
        else:
            city = last_part
            
    return city, state

def clean_group_name(name: str) -> str:
    if not name:
        return name
    
    orig = name
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Check if B Pharma or D Pharma
    name_upper = name.upper()
    if "PHARMA" in name_upper or "B PHARM" in name_upper or "B.PHARM" in name_upper:
        course = "B.Pharma" if "B PHARM" in name_upper or "B.PHARM" in name_upper or "BPHARM" in name_upper else "D.Pharma"
        
        year = "First Year"
        if "2ND" in name_upper or "SECOND" in name_upper or "2nd" in name_upper:
            year = "Second Year"
        elif "3RD" in name_upper or "THIRD" in name_upper or "3rd" in name_upper:
            year = "Third Year"
        elif "4TH" in name_upper or "FOURTH" in name_upper or "4th" in name_upper:
            year = "Fourth Year"
            
        return f"{course}-{year}"
        
    # Standard replacement of roman/ordinal suffixes for Year:
    name = re.sub(r'\b1[sS][tT]\b', '1ST', name)
    name = re.sub(r'\b2[nN][dD]\b', '2nd', name)
    name = re.sub(r'\b3[rR][dD]\b', '3rd', name)
    name = re.sub(r'\b4[tT][hH]\b', '4th', name)
    
    # Replace any separator before SEM with a single space:
    name = re.sub(r'\s*\-?\s*\b(sem|semester|SEM|SEMESTER)\b\s*\-?\s*(\d+)', r' Sem-\2', name)
    
    # Ensure YEAR is uppercase if preceded by ordinal
    name = re.sub(r'\b(year)\b', 'YEAR', name, flags=re.IGNORECASE)
    
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def get_main_course_group(group_name: str) -> str:
    if not group_name:
        return "Other Courses"
    
    # Strip whitespace and normalize
    name_upper = re.sub(r'\s+', ' ', group_name).strip().upper()
    
    if "MCA" in name_upper or "M CA" in name_upper:
        return "MCA"
    if "BCA" in name_upper or "B CA" in name_upper:
        return "BCA"
    if "MBA" in name_upper or "M BA" in name_upper:
        return "MBA"
    if "BBA" in name_upper or "B BA" in name_upper:
        return "BBA"
    if "B.TECH" in name_upper or "BTECH" in name_upper or "B. Tech" in name_upper or "B TECH" in name_upper:
        return "B.Tech"
    if "M.TECH" in name_upper or "MTECH" in name_upper or "M. Tech" in name_upper or "M TECH" in name_upper:
        return "M.Tech"
    if "B.COM" in name_upper or "BCOM" in name_upper or "B. Com" in name_upper or "B COM" in name_upper:
        return "B.Com"
    if "M.COM" in name_upper or "MCOM" in name_upper or "M. Com" in name_upper or "M COM" in name_upper:
        return "M.Com"
    if "B.SC" in name_upper or "BSC" in name_upper or "B. Sc" in name_upper or "B SC" in name_upper:
        return "B.Sc"
    if "M.SC" in name_upper or "MSC" in name_upper or "M. Sc" in name_upper or "M SC" in name_upper:
        return "M.Sc"
    if "B.PHARMA" in name_upper or "BPHARMA" in name_upper or "B PHARM" in name_upper or "B PHARMA" in name_upper:
        return "B.Pharma"
    if "D.PHARMA" in name_upper or "DPHARMA" in name_upper or "D PHARM" in name_upper or "D PHARMA" in name_upper or "D. PHARMACY" in name_upper or "D PHARMACY" in name_upper:
        return "D.Pharma"
    if "LLB" in name_upper or "LLM" in name_upper or "LAW" in name_upper:
        return "Law"
    if "DIPLOMA" in name_upper:
        return "Diploma"
    if "PH.D" in name_upper or "PHD" in name_upper:
        return "PhD"
    if "NURSING" in name_upper or "NURSHING" in name_upper:
        return "Nursing"
    if "DESIGN" in name_upper:
        return "B.Design"
    if "ARCH" in name_upper:
        return "B.Arch"
    if "AGRICULTURE" in name_upper or "AGRONOMY" in name_upper:
        return "Agriculture"
        
    # Default fallback: extract the first alphanumeric word
    words = [w for w in re.split(r'[^A-Za-z0-9\.]', group_name) if w]
    if words:
        first_word = words[0]
        if len(first_word) >= 2:
            return first_word.capitalize()
            
    return "Other Courses"


def extract_year_and_semester(class_name: str) -> tuple:
    if not class_name:
        return "", ""
        
    class_upper = class_name.upper()
    
    # Extract Year
    year = ""
    # Standard mappings
    if any(p in class_upper for p in ("1ST YEAR", "FIRST YEAR", "-1ST", "1ST Y", "1 Y")):
        year = "First Year"
    elif any(p in class_upper for p in ("2ND YEAR", "SECOND YEAR", "-2ND", "2ND Y", "2 Y")):
        year = "Second Year"
    elif any(p in class_upper for p in ("3RD YEAR", "THIRD YEAR", "-3RD", "3RD Y", "3 Y")):
        year = "Third Year"
    elif any(p in class_upper for p in ("4TH YEAR", "FOURTH YEAR", "-4TH", "4TH Y", "4 Y")):
        year = "Fourth Year"
    elif any(p in class_upper for p in ("5TH YEAR", "FIFTH YEAR", "-5TH", "5TH Y", "5 Y")):
        year = "Fifth Year"
        
    # Check for YS patterns like 2YS4
    if not year:
        ys_match = re.search(r'(\d+)\s*YS', class_upper)
        if ys_match:
            y_num = ys_match.group(1)
            mapping = {"1": "First Year", "2": "Second Year", "3": "Third Year", "4": "Fourth Year", "5": "Fifth Year"}
            year = mapping.get(y_num, "")
            
    if not year:
        # Check simple digit before Y or YEAR
        y_digit_match = re.search(r'(\d+)\s*(?:ND|RD|TH|ST)?\s*(?:YEAR|Y\b)', class_upper)
        if y_digit_match:
            y_num = y_digit_match.group(1)
            mapping = {"1": "First Year", "2": "Second Year", "3": "Third Year", "4": "Fourth Year", "5": "Fifth Year"}
            year = mapping.get(y_num, "")

    # Extract Semester
    semester = ""
    # Look for Sem-X or Sem X or Semester X or SEM X
    sem_match = re.search(r'\b(?:SEM|SEMESTER|SEM-)\b\s*-?\s*(\d+)', class_upper)
    if sem_match:
        semester = f"Sem-{sem_match.group(1)}"
    else:
        # Check for YS pattern like 2YS4 (4 is the semester)
        ys_sem_match = re.search(r'\d+\s*YS\s*(\d+)', class_upper)
        if ys_sem_match:
            semester = f"Sem-{ys_sem_match.group(1)}"
        else:
            # Fallback to check word list like "1ND SEM", "2ND SEM", etc.
            sem_ord = re.search(r'(\d+)(?:ST|ND|RD|TH)\s*SEM', class_upper)
            if sem_ord:
                semester = f"Sem-{sem_ord.group(1)}"
            else:
                # Check for "SEM- X" or "SEM X"
                sem_simple = re.search(r'SEM\s*(\d+)', class_upper)
                if sem_simple:
                    semester = f"Sem-{sem_simple.group(1)}"
                    
    return year, semester


def split_address(addr_str: str, max_lines: int = 4, line_len: int = 40) -> list:
    if not addr_str:
        return []
    raw_lines = [line.strip() for line in addr_str.replace('\r', '').split('\n') if line.strip()]
    lines = []
    for raw_line in raw_lines:
        while len(raw_line) > line_len:
            split_idx = raw_line.rfind(' ', 0, line_len)
            if split_idx == -1:
                split_idx = raw_line.rfind(',', 0, line_len)
            if split_idx == -1 or split_idx < 10:
                split_idx = line_len
            lines.append(raw_line[:split_idx].strip())
            raw_line = raw_line[split_idx:].strip()
        if raw_line:
            lines.append(raw_line)
    return lines[:max_lines]


class TallyClient:
    def __init__(self, base_url: str = None):
        """
        Initializes Tally API client targeting local XML HTTP server.
        """
        self.base_url = base_url or settings.TALLY_URL
        self.company = settings.TALLY_COMPANY
        self.headers = {"Content-Type": "text/xml; charset=utf-8"}
        self._verified_groups = set()
        self.username = getattr(settings, 'TALLY_USERNAME', '')
        self.password = getattr(settings, 'TALLY_PASSWORD', '')

    def _post(self, url, data, timeout=30):
        if self.username and self.password:
            return requests.post(url, data=data, headers=self.headers, timeout=timeout, auth=(self.username, self.password))
        else:
            return requests.post(url, data=data, headers=self.headers, timeout=timeout)
        
    def fetch_student_details(self, retries: int = 3, backoff_factor: float = 1.5) -> str:
        """
        Sends StudentDetail XML export query payload to local Tally gateway.
        Implements robust exception filters and backoff retry logic.
        """
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
    <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""

        url = self.base_url
        logger.debug(f"Querying Tally API endpoint: {url} ...")
        
        for attempt in range(1, retries + 1):
            try:
                # 60s timeout for large data lists
                response = self._post(url, data=payload, timeout=60)
                response.raise_for_status()
                
                content = response.text
                if not content or not content.strip():
                    raise ValueError("Tally returned an empty response.")
                    
                # Scan for unhandled TTDL execution logs or connection locks
                if "<LINEERROR>" in content or "<ERRORTEXT>" in content:
                    logger.error(f"Tally integration error response detected: {content[:500]}")
                    raise ValueError("Tally server returned an internal transaction or TDL script compilation/execution error.")
                    
                logger.info(f"Successfully retrieved XML data from Tally: {len(response.content)} bytes")
                return content
                
            except (ConnectionError, Timeout) as e:
                logger.warning(f"Connection attempt {attempt}/{retries} failed for Tally at {url}: {str(e)}")
                if attempt == retries:
                    logger.error("Maximum Tally connection retries exhausted. Check if Tally is running and port is correct.")
                    raise ConnectionError(f"Failed to establish connection with local Tally server at {url} after {retries} attempts.")
                time.sleep(backoff_factor ** attempt)
                
            except HTTPError as e:
                logger.error(f"HTTP transaction error from Tally: {str(e)}")
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error communicating with Tally server: {str(e)}")
                raise

    def fetch_transactions(self, retries: int = 3, backoff_factor: float = 1.5) -> str:
        """
        Fetches all transactions using the Tally Voucher Register report which is optimized
        and prevents the HTTP timeout errors seen with raw Collection queries.
        """
        payload = f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Voucher Register</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
        
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Fetching transactions from Tally using Voucher Register (Attempt {attempt})...")
                # Use a larger timeout for transactions just in case (60s)
                response = self._post(self.base_url, data=payload, timeout=60)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching transactions from Tally: {str(e)}")
                if attempt < retries:
                    sleep_time = backoff_factor ** attempt
                    logger.info(f"Retrying transaction fetch in {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error("Max retries reached. Could not fetch transactions from Tally.")
                    return ""

    def fetch_all_ledger_names(self, retries: int = 3, backoff_factor: float = 1.5) -> set:
        """
        Queries Tally for a collection of all ledger names and aliases.
        Returns a set of all names and aliases (lowercased).
        """
        payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>List of Ledgers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
   <TDL>
    <TDLUSERLIST TYPE="Collection" NAME="List of Ledgers">
     <TYPE>Ledger</TYPE>
    </TDLUSERLIST>
   </TDL>
  </DESC>
 </BODY>
</ENVELOPE>"""
        url = self.base_url
        logger.debug("Fetching all ledger names and aliases from Tally for fallback check...")
        
        for attempt in range(1, retries + 1):
            try:
                response = self._post(url, data=payload, timeout=30)
                response.raise_for_status()
                content = response.text
                if not content or not content.strip():
                    raise ValueError("Tally returned empty response for ledgers list.")
                
                import xml.etree.ElementTree as ET
                xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
                root = ET.fromstring(xml_clean.strip().encode('utf-8'))
                
                names = set()
                for led in root.findall(".//LEDGER"):
                    name_attr = led.get("NAME")
                    if name_attr:
                        names.add(name_attr.strip().lower())
                    for name_elem in led.findall(".//NAME"):
                        if name_elem.text:
                            names.add(name_elem.text.strip().lower())
                logger.debug(f"Retrieved {len(names)} unique names/aliases from Tally.")
                return names
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Failed to fetch ledger names from Tally: {e}")
                    raise
                time.sleep(backoff_factor ** attempt)
        return set()

    def fetch_all_ledgers_with_parent(self, retries: int = 3, backoff_factor: float = 1.5) -> dict:
        """
        Queries Tally for a collection of all ledger names and their parent groups.
        Returns a dict of {ledger_name: parent_group} (keys in lowercase, values as-is but stripped).
        """
        payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>Ledger</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
        url = self.base_url
        logger.debug("Fetching all ledger names and parents from Tally...")
        
        for attempt in range(1, retries + 1):
            try:
                response = self._post(url, data=payload, timeout=30)
                response.raise_for_status()
                content = response.text
                if not content or not content.strip():
                    raise ValueError("Tally returned empty response for ledgers list.")
                
                import xml.etree.ElementTree as ET
                xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
                xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
                root = ET.fromstring(xml_clean.strip().encode('utf-8'))
                
                ledger_map = {}
                for led in root.findall(".//LEDGER"):
                    name_attr = led.get("NAME")
                    parent_elem = led.find(".//PARENT")
                    parent = parent_elem.text.strip() if parent_elem is not None and parent_elem.text else "Sundry Debtors"
                    
                    if name_attr:
                        ledger_map[name_attr.strip().lower()] = parent
                    
                    for name_elem in led.findall(".//NAME"):
                        if name_elem.text:
                            ledger_map[name_elem.text.strip().lower()] = parent
                            
                logger.debug(f"Retrieved {len(ledger_map)} ledger mappings from Tally.")
                return ledger_map
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Failed to fetch ledger mappings from Tally: {e}")
                    raise
                time.sleep(backoff_factor ** attempt)
        return {}

    def fetch_all_ledgers_primary_names(self, retries: int = 3, backoff_factor: float = 1.5) -> dict:
        """
        Queries Tally for a collection of all ledger names.
        Returns a dict of {lowercase_alias_or_name: current_primary_name}
        """
        payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>Ledger</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
        url = self.base_url
        logger.debug("Fetching all ledger primary names from Tally...")
        
        for attempt in range(1, retries + 1):
            try:
                response = self._post(url, data=payload, timeout=30)
                response.raise_for_status()
                content = response.text
                if not content or not content.strip():
                    raise ValueError("Tally returned empty response for ledgers list.")
                
                import xml.etree.ElementTree as ET
                xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
                xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
                root = ET.fromstring(xml_clean.strip().encode('utf-8'))
                
                primary_map = {}
                for led in root.findall(".//LEDGER"):
                    primary_name = led.get("NAME")
                    if not primary_name:
                        continue
                    
                    primary_name_str = primary_name.strip()
                    primary_map[primary_name_str.lower()] = primary_name_str
                    
                    for name_elem in led.findall(".//NAME"):
                        if name_elem.text:
                            primary_map[name_elem.text.strip().lower()] = primary_name_str
                            
                logger.debug(f"Retrieved {len(primary_map)} ledger primary name mappings from Tally.")
                return primary_map
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Failed to fetch ledger primary name mappings from Tally: {e}")
                    raise
                time.sleep(backoff_factor ** attempt)
        return {}

    def get_ledger_parent(self, name_or_alias: str) -> str:
        """
        Queries Tally for a single ledger by name or enrollment number (alias)
        and returns its parent group name. Returns None if ledger does not exist.
        """
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
    <SVOBJECTNAME>{name_or_alias}</SVOBJECTNAME>
    <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
        try:
            response = self._post(self.base_url, data=payload, timeout=5)
            response.raise_for_status()
            content = response.text
            if not content or not content.strip() or "<PARENT>" not in content:
                return None
                
            import xml.etree.ElementTree as ET
            # clean up invalid XML characters if any
            xml_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', content)
            xml_clean = re.sub(r'&#x?[0-9a-fA-F]+;', '', xml_clean)
            root = ET.fromstring(xml_clean.strip().encode('utf-8'))
            
            parent_elem = root.find(".//PARENT")
            if parent_elem is not None and parent_elem.text:
                return parent_elem.text.strip()
            return None
        except Exception as e:
            logger.error(f"Error checking single ledger parent for '{name_or_alias}': {e}")
            return None


    def create_group_in_tally(self, group_name: str) -> bool:
        """
        Creates a missing parent group in Tally with proper hierarchy:
        - "Student" is under "Sundry Debtors"
        - Main Course groups (e.g. BBA, MCA, BCA, B.Tech, MBA, B.Sc) are under "Student"
        - Semester/Year specific subgroups (e.g. BBA 1ST YEAR Sem-1) are under their respective Main Course group
        """
        if not group_name:
            return False

        group_name = group_name.strip()
        if group_name in self._verified_groups:
            return True

        # Determine the parent group
        main_course = get_main_course_group(group_name)
        
        if group_name == "Student":
            parent_group = "Sundry Debtors"
        elif group_name == main_course:
            parent_group = "Student"
            # Ensure "Student" exists
            self.create_group_in_tally("Student")
        else:
            parent_group = main_course
            # Ensure the parent main course group exists under "Student"
            self.create_group_in_tally(main_course)

        payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Import</TALLYREQUEST>
  <TYPE>Data</TYPE>
  <ID>All Masters</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
  <DATA>
   <TALLYMESSAGE xmlns:UDF="TallyUDF">
    <GROUP NAME="{escape_xml(group_name)}" ACTION="Create">
     <NAME>{escape_xml(group_name)}</NAME>
     <PARENT>{escape_xml(parent_group)}</PARENT>
    </GROUP>
   </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>"""
        try:
            response = self._post(self.base_url, data=payload, timeout=10)
            response.raise_for_status()
            content = response.text
            if "<CREATED>1</CREATED>" in content or "<ALTERED>1</ALTERED>" in content or "<COMBINED>1</COMBINED>" in content:
                logger.info(f"Successfully created parent group '{group_name}' under '{parent_group}' in Tally.")
                self._verified_groups.add(group_name)
                return True
            # Tally might say "Already Exists" inside an error or response, which is fine!
            if "Already Exists" in content or "already exists" in content or "Duplicate" in content:
                logger.debug(f"Group '{group_name}' already exists in Tally.")
                self._verified_groups.add(group_name)
                return True
            logger.error(f"Failed to create group '{group_name}' in Tally. Response: {content}")
            return False
        except Exception as e:
            logger.error(f"Error creating group '{group_name}' in Tally: {e}")
            return False

    def sync_student_to_tally(self, enrollment_no: str, student_data: dict, is_new: bool = False, tally_ledger_name: str = None, _retry_count: int = 0) -> bool:
        """
        Sends an Import Data XML transaction to create or alter a student ledger in Tally.
        - enrollment_no: unique student primary key (alias in Tally).
        - student_data: dict of student columns to sync.
        - is_new: boolean indicating if this is a newly created ledger.
        """
        # Determine the action: Create for brand new ledgers, Alter for existing ones
        action = "Create" if is_new else "Alter"
        
        student_name = student_data.get("student_name")
        if student_name:
            suffix = f"-{enrollment_no}"
            if not student_name.strip().endswith(suffix):
                ledger_name = f"{student_name.strip()} -{enrollment_no}"
            else:
                ledger_name = student_name.strip()
        else:
            ledger_name = enrollment_no

        # Extract clean student name (without enrollment suffix) for mailing name
        clean_name = ledger_name
        if enrollment_no:
            pattern = re.compile(rf'\s*-\s*{re.escape(enrollment_no)}\s*$', re.IGNORECASE)
            clean_name = pattern.sub('', clean_name).strip()

        xml_parts = []
        
        # Add primary NAME tag inside LEDGER so Tally updates the primary ledger name
        xml_parts.append(f"     <NAME>{escape_xml(ledger_name)}</NAME>")
        
        # Add OLDMAILINGNAME.LIST (used by custom alteration screens/reports to read student name)
        xml_parts.append(f"""     <OLDMAILINGNAME.LIST TYPE="String">
      <OLDMAILINGNAME>{escape_xml(clean_name)}</OLDMAILINGNAME>
     </OLDMAILINGNAME.LIST>""")
        
        # Always include the Name List inside LANGUAGENAME.LIST
        xml_parts.append(f"""     <LANGUAGENAME.LIST>
      <NAME.LIST TYPE="String">
       <NAME>{escape_xml(ledger_name)}</NAME>
       <NAME>{escape_xml(enrollment_no)}</NAME>
      </NAME.LIST>
      <LANGUAGEID>1033</LANGUAGEID>
     </LANGUAGENAME.LIST>""")

        xml_parts.append(f"     <MAILINGNAME>{escape_xml(clean_name)}</MAILINGNAME>")

        student_class = student_data.get("student_class")
        if student_class:
            student_class = clean_group_name(student_class)
            
        import datetime
        current_year = datetime.datetime.now().year
        
        status = str(student_data.get("status") or "").strip().upper()
        is_left_bool = student_data.get("is_left") in (True, "true", "True", "yes", "Yes", 1, "1")
        
        if status == 'P':
            xml_parts.append(f"     <PARENT>Passout {current_year}</PARENT>")
        elif status == 'L' or is_left_bool:
            xml_parts.append(f"     <PARENT>Left {current_year}</PARENT>")
        elif student_class:
            xml_parts.append(f"     <PARENT>{escape_xml(student_class)}</PARENT>")
        else:
            xml_parts.append("     <PARENT>Sundry Debtors</PARENT>")

        balance_val = None
        if "opening_balance" in student_data:
            balance_val = student_data["opening_balance"]
        elif "closing_balance" in student_data:
            balance_val = student_data["closing_balance"]
            
        if balance_val is not None:
            try:
                tally_balance = -float(balance_val)
                xml_parts.append(f"     <OPENINGBALANCE>{tally_balance:.2f}</OPENINGBALANCE>")
            except (ValueError, TypeError):
                pass

        if "billwise" in student_data:
            val = "Yes" if student_data["billwise"] else "No"
            xml_parts.append(f"     <ISBILLWISEON>{val}</ISBILLWISEON>")

        # Email field
        email = student_data.get("email")
        if email:
            xml_parts.append(f"     <EMAIL>{escape_xml(email)}</EMAIL>")

        # Extra address-related details
        p_addr = student_data.get("permanent_address")
        p_city, p_state = parse_city_state(p_addr)
        
        c_addr = student_data.get("correspondence_address")
        c_city, c_state = parse_city_state(c_addr)
        c_pin = student_data.get("correspondence_pin")
        
        # Add UDFs for Permanent address details
        p_city_val = p_city if p_city else ""
        xml_parts.append(f"""     <UDF:PERMTCITY.LIST DESC="`PermtCity`" ISLIST="YES" TYPE="String">
      <UDF:PERMTCITY DESC="`PermtCity`">{escape_xml(p_city_val)}</UDF:PERMTCITY>
     </UDF:PERMTCITY.LIST>""")
        
        state_udf = ""
        if p_state:
            state_udf = "UP" if p_state == "Uttar Pradesh" else p_state
        xml_parts.append(f"""     <UDF:PERMTSTATE.LIST DESC="`PermtState`" ISLIST="YES" TYPE="String">
      <UDF:PERMTSTATE DESC="`PermtState`">{escape_xml(state_udf)}</UDF:PERMTSTATE>
     </UDF:PERMTSTATE.LIST>""")
     
        country_udf = "INDIA" if (p_addr and str(p_addr).strip().lower() not in ("none", "null", "nan")) else ""
        xml_parts.append(f"""     <UDF:PERMTCOUNTRY.LIST DESC="`PermtCountry`" ISLIST="YES" TYPE="String">
      <UDF:PERMTCOUNTRY DESC="`PermtCountry`">{escape_xml(country_udf)}</UDF:PERMTCOUNTRY>
     </UDF:PERMTCOUNTRY.LIST>""")

        # Add UDFs for Correspondence address details
        c_city_val = c_city if c_city else ""
        xml_parts.append(f"""     <UDF:CORSCITY.LIST DESC="`CorsCity`" ISLIST="YES" TYPE="String">
      <UDF:CORSCITY DESC="`CorsCity`">{escape_xml(c_city_val)}</UDF:CORSCITY>
     </UDF:CORSCITY.LIST>""")
     
        c_state_udf = ""
        if c_state:
            c_state_udf = "UP" if c_state == "Uttar Pradesh" else c_state
        xml_parts.append(f"""     <UDF:CORSSTATE.LIST DESC="`CorsState`" ISLIST="YES" TYPE="String">
      <UDF:CORSSTATE DESC="`CorsState`">{escape_xml(c_state_udf)}</UDF:CORSSTATE>
     </UDF:CORSSTATE.LIST>""")

        # Standard correspondence address at ledger level
        c_addr_lines = split_address(c_addr)
        if c_addr_lines:
            xml_parts.append("     <ADDRESS.LIST TYPE=\"String\">")
            for line in c_addr_lines:
                xml_parts.append(f"      <ADDRESS>{escape_xml(line)}</ADDRESS>")
            xml_parts.append("     </ADDRESS.LIST>")
            
        if c_pin:
            xml_parts.append(f"     <PINCODE>{escape_xml(c_pin)}</PINCODE>")

        # Standard LEDMAILINGDETAILS.LIST
        mailing_parts = []
        # Add APPLICABLEFROM date (Tally needs this to store/display the mailing details list)
        mailing_parts.append("      <APPLICABLEFROM>20220401</APPLICABLEFROM>")
        mailing_parts.append(f"      <MAILINGNAME>{escape_xml(clean_name)}</MAILINGNAME>")
        if c_state:
            mailing_parts.append(f"      <STATE>{escape_xml(c_state)}</STATE>")
        mailing_parts.append("      <COUNTRY>India</COUNTRY>")
        if c_pin:
            mailing_parts.append(f"      <PINCODE>{escape_xml(c_pin)}</PINCODE>")
        if email:
            mailing_parts.append(f"      <EMAIL>{escape_xml(email)}</EMAIL>")
        if c_addr_lines:
            mailing_parts.append("      <ADDRESS.LIST TYPE=\"String\">")
            for line in c_addr_lines:
                mailing_parts.append(f"       <ADDRESS>{escape_xml(line)}</ADDRESS>")
            mailing_parts.append("      </ADDRESS.LIST>")
            
        mailing_parts_str = "\n".join(mailing_parts)
        xml_parts.append(f"""     <LEDMAILINGDETAILS.LIST>
{mailing_parts_str}
     </LEDMAILINGDETAILS.LIST>""")

        # Extract year and semester from student_class
        class_val = student_data.get("student_class") or ""
        extracted_year, extracted_sem = extract_year_and_semester(class_val)
        
        # Add direct TDL tags for custom screens
        xml_parts.append(f"     <KGSTUDCLASS>{escape_xml(class_val)}</KGSTUDCLASS>")
        xml_parts.append(f"     <KGYEAR>{escape_xml(extracted_year)}</KGYEAR>")
        xml_parts.append(f"     <KGSEMESTER>{escape_xml(extracted_sem)}</KGSEMESTER>")
        xml_parts.append(f"     <KGENRNO>{escape_xml(enrollment_no)}</KGENRNO>")
        xml_parts.append(f"     <KGCOURSE>{escape_xml(student_data.get('course') or '')}</KGCOURSE>")
        xml_parts.append(f"     <KGSESSION>{escape_xml(student_data.get('session') or '')}</KGSESSION>")
        xml_parts.append(f"     <KGFATHERNAME>{escape_xml(student_data.get('father_name') or '')}</KGFATHERNAME>")
        xml_parts.append(f"     <KGMOTHERNAME>{escape_xml(student_data.get('mother_name') or '')}</KGMOTHERNAME>")
        xml_parts.append(f"     <KGROLLNO>{escape_xml(student_data.get('roll_no') or '')}</KGROLLNO>")
        xml_parts.append(f"     <KGREGTNO>{escape_xml(student_data.get('registration_no') or '')}</KGREGTNO>")
        
        dob_val = student_data.get('dob') or ''
        if dob_val:
            dob_val = str(dob_val).split(" ")[0].replace("-", "")
        xml_parts.append(f"     <KGDOB>{escape_xml(dob_val)}</KGDOB>")
        
        gender_val = student_data.get('gender') or ''
        xml_parts.append(f"     <KGSEX>{escape_xml(gender_val)}</KGSEX>")
        xml_parts.append(f"     <KGMOBNO>{escape_xml(student_data.get('mobile') or '')}</KGMOBNO>")
        xml_parts.append(f"     <KGEMAL>{escape_xml(student_data.get('email') or '')}</KGEMAL>")
        xml_parts.append(f"     <KGSTATUS>{escape_xml(student_data.get('status') or '')}</KGSTATUS>")
        
        # Populate year, semester, and session duplicates for UDFs in Tally
        student_data["year"] = extracted_year
        student_data["semester"] = extracted_sem
        if "session" in student_data and student_data["session"] is not None:
            student_data["session_yrdisc"] = student_data["session"]
            student_data["session_kg"] = student_data["session"]

        udf_mapping = {
            "father_name": ("IMFTHNAME", "IMFthName", "String"),
            "mother_name": ("IMMTHNAME", "IMMthName", "String"),
            "religion": ("IMSTDRELIGION", "IMStdReligion", "String"),
            "gender": ("SEX", "Sex", "String"),
            "roll_no": ("IMROLLNO", "IMRollNo", "String"),
            "course": ("IMCOURSE", "IMCourse", "String"),
            "session": ("IMSESSION", "IMSession", "String"),
            "session_yrdisc": ("YRDISCSESSION", "YRDiscSession", "String"),
            "session_kg": ("KGSESSION", "KGSession", "String"),
            "year": ("IMYEAR", "IMYEar", "String"),
            "student_class": ("STDADMCLASS", "StdAdmClass", "String"),
            "mobile": ("CORSMOBILENO", "CorsMobileNo", "String"),
            "caste": ("IMSTDCASTE", "IMStdCaste", "String"),
            "category": ("STDCATEGORY", "StdCategory", "String"),
            "registration_no": ("IMREGTNO", "IMRegtNo", "String"),
            "dob": ("MDOB", "MDOB", "Date"),
            "admission_category": ("ADMCATEGORY", "AdmCategory", "String"),
            "rank": ("IMSTDRANK", "IMStdRank", "String"),
            "annual_income": ("ANNUALINCOMEOFPARENT", "AnnualIncomeOfParent", "String"),
            "permanent_pin": ("PERMTPINCODE", "PermtPinCode", "String"),
            "correspondence_pin": ("CORSPINCODE", "CorsPinCode", "String"),
            "permanent_address": ("OFFICEADDRESS", "OfficeAddress", "String"),
            "quota": ("QUOTALED", "QuotaLed", "String"),
            "status": ("IMSTDSTATUS", "IMStdStatus", "String"),
            "email": ("KGEMAL", "KGEmal", "String"),
        }

        for db_col, (udf_tag, udf_desc, udf_type) in udf_mapping.items():
            if db_col in student_data and student_data[db_col] is not None:
                val = str(student_data[db_col]).strip()
                if udf_type == "Date" and val:
                    val = val.split(" ")[0].replace("-", "")
                xml_parts.append(f"""     <UDF:{udf_tag}.LIST DESC="`{udf_desc}`" ISLIST="YES" TYPE="{udf_type}">
      <UDF:{udf_tag} DESC="`{udf_desc}`">{escape_xml(val)}</UDF:{udf_tag}>
     </UDF:{udf_tag}.LIST>""")

        inner_xml = "\n".join(xml_parts)
        target_identifier = tally_ledger_name if (tally_ledger_name and not is_new) else ledger_name

        payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Import</TALLYREQUEST>
  <TYPE>Data</TYPE>
  <ID>All Masters</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
    <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
  <DATA>
   <TALLYMESSAGE xmlns:UDF="TallyUDF">
    <LEDGER NAME="{target_identifier}" ACTION="{action}">
{inner_xml}
    </LEDGER>
   </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>"""

        url = self.base_url
        logger.debug(f"Sending student sync request to Tally ({action} {enrollment_no})...")
        
        try:
            response = self._post(url, data=payload, timeout=30)
            response.raise_for_status()
            
            content = response.text
            if not content or not content.strip():
                raise ValueError("Tally returned an empty response.")
                
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(content.strip())
                import_result = root.find(".//IMPORTRESULT")
                if import_result is not None:
                    errors = import_result.find("ERRORS")
                    exceptions = import_result.find("EXCEPTIONS")
                    err_count = int(errors.text) if errors is not None else 0
                    exc_count = int(exceptions.text) if exceptions is not None else 0
                    if err_count == 0 and exc_count == 0:
                        logger.info(f"Successfully synced student {enrollment_no} to Tally ({action}).")
                        return True
                    else:
                        # Self-healing retry: Check for missing parent group error
                        if _retry_count == 0 and ("Group &apos;" in content or "Group '" in content) and "does not exist!" in content:
                            match = re.search(r"Group &apos;(.+?)&apos; does not exist!", content)
                            if not match:
                                match = re.search(r"Group '([^']+)' does not exist!", content)
                            if match:
                                import html
                                missing_group = html.unescape(match.group(1))
                                logger.warning(f"Tally student sync failed due to missing group '{missing_group}'. Attempting auto-creation...")
                                if self.create_group_in_tally(missing_group):
                                    return self.sync_student_to_tally(enrollment_no, student_data, is_new=is_new, _retry_count=1)
                        
                        logger.error(f"Tally import returned errors: {err_count}, exceptions: {exc_count}. Response content: {content}")
                        return False
                if "<LINEERROR>" in content or "<ERRORTEXT>" in content:
                    # Also try self-healing for raw LINEERROR messages
                    if _retry_count == 0 and ("Group &apos;" in content or "Group '" in content) and "does not exist!" in content:
                        match = re.search(r"Group &apos;(.+?)&apos; does not exist!", content)
                        if not match:
                            match = re.search(r"Group '([^']+)' does not exist!", content)
                        if match:
                            import html
                            missing_group = html.unescape(match.group(1))
                            logger.warning(f"Tally student sync failed (LineError) due to missing group '{missing_group}'. Attempting auto-creation...")
                            if self.create_group_in_tally(missing_group):
                                return self.sync_student_to_tally(enrollment_no, student_data, is_new=is_new, _retry_count=1)
                    
                    logger.error(f"Tally response error: {content}")
                    return False
            except Exception as parse_err:
                logger.error(f"Failed to parse Tally response XML: {str(parse_err)}. Content: {content[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Error communicating with Tally during realtime sync of {enrollment_no}: {str(e)}")
            return False
        
        return False

    def sync_transaction_to_tally(self, transaction_data: dict) -> bool:
        """
        Sends an Import Data XML transaction to create or alter a voucher in Tally.
        Requires full transaction_data including 'fee_allocations' and 'students' nested data.
        """
        action = "Alter"
        guid = transaction_data.get("guid")
        vch_type = transaction_data.get("voucher_type", "Due Fee")
        
        tx_date = transaction_data.get("date")
        if tx_date:
            date_raw = tx_date.replace("-", "")
        else:
            date_raw = "20250401"
            
        vch_num = transaction_data.get("voucher_number", "")
        
        party_ledger = transaction_data.get("party_ledger_name")
        if not party_ledger:
            student = transaction_data.get("students", {})
            student_name = student.get("student_name", "")
            enrollment_no = transaction_data.get("enrollment_no", "")
            if student_name and enrollment_no:
                party_ledger = f"{student_name.strip()} -{enrollment_no}"
            else:
                party_ledger = enrollment_no
                
        amount = float(transaction_data.get("amount", 0.0))
        allocations = transaction_data.get("fee_allocations", [])
        
        xml_parts = []
        xml_parts.append(f"""     <GUID>{guid}</GUID>
     <DATE>{date_raw}</DATE>
     <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
     <VOUCHERNUMBER>{vch_num}</VOUCHERNUMBER>
     <PARTYLEDGERNAME>{party_ledger}</PARTYLEDGERNAME>
     <CSTFORMISSUETYPE/>
     <CSTFORMRECVTYPE/>
     <FBTPAYMENTTYPE>Default</FBTPAYMENTTYPE>
     <PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>
     <VCHGSTCLASS/>
     <DIFFACTUALQTY>No</DIFFACTUALQTY>
     <ISMSTFROMSYNC>No</ISMSTFROMSYNC>
     <ASORIGINAL>No</ASORIGINAL>
     <AUDITED>No</AUDITED>
     <FORJOBCOSTING>No</FORJOBCOSTING>
     <ISOPTIONAL>No</ISOPTIONAL>
     <EFFECTIVEDATE>{date_raw}</EFFECTIVEDATE>
     <USEFOREXCISE>No</USEFOREXCISE>
     <ISFORJOBWORKIN>No</ISFORJOBWORKIN>
     <ALLOWCONSUMPTION>No</ALLOWCONSUMPTION>
     <USEFORINTEREST>No</USEFORINTEREST>
     <USEFORGAINLOSS>No</USEFORGAINLOSS>
     <USEFORGODOWNTRANSFER>No</USEFORGODOWNTRANSFER>
     <USEFORCOMPOUND>No</USEFORCOMPOUND>
     <USEFORSERVICETAX>No</USEFORSERVICETAX>
     <ISEXCISEVOUCHER>No</ISEXCISEVOUCHER>
     <EXCISETAXOVERRIDE>No</EXCISETAXOVERRIDE>
     <USEFORTAXES>No</USEFORTAXES>
     <IGNOREPOSVCH>No</IGNOREPOSVCH>
     <NONTAXABLETOLL>No</NONTAXABLETOLL>
     <EXCLUDEDTAXATIONS.LIST>      </EXCLUDEDTAXATIONS.LIST>
     <STATUTORYDETAILS.LIST>      </STATUTORYDETAILS.LIST>""")

        if vch_type == "Due Fee":
            # For Due Fee (Journal/Fee Due):
            # Student is Debited (ISDEEMEDPOSITIVE = Yes, amount is negative in Tally)
            party_amount_str = f"{-amount:.2f}"
            party_deemed_positive = "Yes"
            
            # Build Party entry
            party_entry = f"""      <LEDGERNAME>{party_ledger}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>{party_deemed_positive}</ISDEEMEDPOSITIVE>
       <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
       <AMOUNT>{party_amount_str}</AMOUNT>"""
       
            allocs_xml = []
            for alloc in allocations:
                bill_name = alloc.get("bill_name", "")
                bill_amt = float(alloc.get("amount", 0.0))
                # For debit, bill allocation amount is also negative in Tally
                bill_amt_str = f"{-bill_amt:.2f}"
                bill_type = alloc.get("bill_type", "New Ref")
                fee_head = alloc.get("fee_head", "")
                semester = alloc.get("semester", "")
                
                alloc_xml = f"""       <BILLALLOCATIONS.LIST>
        <NAME>{bill_name}</NAME>
        <BILLTYPE>{bill_type}</BILLTYPE>
        <AMOUNT>{bill_amt_str}</AMOUNT>"""
                if fee_head:
                    alloc_xml += f"""
        <UDF:VCHBILLFEENAME.LIST DESC="`VchBillFeeName`" ISLIST="YES" TYPE="String" INDEX="8182">
         <UDF:VCHBILLFEENAME DESC="`VchBillFeeName`">{fee_head}</UDF:VCHBILLFEENAME>
        </UDF:VCHBILLFEENAME.LIST>"""
                if semester:
                    alloc_xml += f"""
        <UDF:VCHBILLSEMNAME.LIST DESC="`VchBillSemName`" ISLIST="YES" TYPE="String" INDEX="8183">
         <UDF:VCHBILLSEMNAME DESC="`VchBillSemName`">{semester}</UDF:VCHBILLSEMNAME>
        </UDF:VCHBILLSEMNAME.LIST>"""
                alloc_xml += "\n       </BILLALLOCATIONS.LIST>"
                allocs_xml.append(alloc_xml)
                
            allocs_str = "\n".join(allocs_xml)
            xml_parts.append(f"""     <ALLLEDGERENTRIES.LIST>
{party_entry}
{allocs_str}
     </ALLLEDGERENTRIES.LIST>""")

            # Add Credit Balancing Entries for each fee head
            for alloc in allocations:
                bill_amt = float(alloc.get("amount", 0.0))
                bill_amt_str = f"{bill_amt:.2f}"
                fee_head = alloc.get("fee_head", "")
                if not fee_head:
                    fee_head = "TUTION FEE" # Fallback if empty
                    
                xml_parts.append(f"""     <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>{fee_head}</LEDGERNAME>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <ISPARTYLEDGER>No</ISPARTYLEDGER>
      <AMOUNT>{bill_amt_str}</AMOUNT>
     </ALLLEDGERENTRIES.LIST>""")
        else:
            # For Fees Receipt (Receipt/Payment):
            # Student is Credited (ISDEEMEDPOSITIVE = No, amount is positive)
            party_amount_str = f"{amount:.2f}"
            party_deemed_positive = "No"
            
            # Build Party entry
            party_entry = f"""      <LEDGERNAME>{party_ledger}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>{party_deemed_positive}</ISDEEMEDPOSITIVE>
       <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
       <AMOUNT>{party_amount_str}</AMOUNT>"""
       
            allocs_xml = []
            for alloc in allocations:
                bill_name = alloc.get("bill_name", "")
                bill_amt = float(alloc.get("amount", 0.0))
                bill_amt_str = f"{bill_amt:.2f}"
                bill_type = alloc.get("bill_type", "New Ref")
                fee_head = alloc.get("fee_head", "")
                semester = alloc.get("semester", "")
                
                alloc_xml = f"""       <BILLALLOCATIONS.LIST>
        <NAME>{bill_name}</NAME>
        <BILLTYPE>{bill_type}</BILLTYPE>
        <AMOUNT>{bill_amt_str}</AMOUNT>"""
                if fee_head:
                    alloc_xml += f"""
        <UDF:VCHBILLFEENAME.LIST DESC="`VchBillFeeName`" ISLIST="YES" TYPE="String" INDEX="8182">
         <UDF:VCHBILLFEENAME DESC="`VchBillFeeName`">{fee_head}</UDF:VCHBILLFEENAME>
        </UDF:VCHBILLFEENAME.LIST>"""
                if semester:
                    alloc_xml += f"""
        <UDF:VCHBILLSEMNAME.LIST DESC="`VchBillSemName`" ISLIST="YES" TYPE="String" INDEX="8183">
         <UDF:VCHBILLSEMNAME DESC="`VchBillSemName`">{semester}</UDF:VCHBILLSEMNAME>
        </UDF:VCHBILLSEMNAME.LIST>"""
                alloc_xml += "\n       </BILLALLOCATIONS.LIST>"
                allocs_xml.append(alloc_xml)
                
            allocs_str = "\n".join(allocs_xml)
            xml_parts.append(f"""     <ALLLEDGERENTRIES.LIST>
{party_entry}
{allocs_str}
     </ALLLEDGERENTRIES.LIST>""")

            # Add Cash Balancing Entry
            cash_amount_str = f"{-amount:.2f}"
            xml_parts.append(f"""     <ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>Cash</LEDGERNAME>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
      <AMOUNT>{cash_amount_str}</AMOUNT>
     </ALLLEDGERENTRIES.LIST>""")

        inner_xml = "\n".join(xml_parts)

        payload = f"""<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>Import</TALLYREQUEST>
  <TYPE>Data</TYPE>
  <ID>Vouchers</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
  </DESC>
  <DATA>
   <TALLYMESSAGE xmlns:UDF="TallyUDF">
     <VOUCHER REMOTEID="{guid}" VCHTYPE="{vch_type}" ACTION="{action}">
{inner_xml}
     </VOUCHER>
    </TALLYMESSAGE>
  </DATA>
 </BODY>
</ENVELOPE>"""

        url = self.base_url
        logger.debug(f"Sending voucher sync request to Tally ({action} {guid})...")
        
        try:
            response = self._post(url, data=payload, timeout=30)
            response.raise_for_status()
            
            content = response.text
            if not content or not content.strip():
                raise ValueError("Tally returned an empty response.")
                
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(content.strip())
                import_result = root.find(".//IMPORTRESULT")
                if import_result is not None:
                    errors = import_result.find("ERRORS")
                    exceptions = import_result.find("EXCEPTIONS")
                    err_count = int(errors.text) if errors is not None else 0
                    exc_count = int(exceptions.text) if exceptions is not None else 0
                    if err_count == 0 and exc_count == 0:
                        logger.info(f"Successfully synced transaction {guid} to Tally ({action}).")
                        return True
                    else:
                        logger.error(f"Tally import returned errors: {err_count}, exceptions: {exc_count}. Response content: {content}")
                        return False
                if "<LINEERROR>" in content or "<ERRORTEXT>" in content:
                    logger.error(f"Tally response error: {content}")
                    return False
            except Exception as parse_err:
                logger.error(f"Failed to parse Tally response XML: {str(parse_err)}. Content: {content[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Error communicating with Tally during realtime sync of voucher {guid}: {str(e)}")
            return False
        
        return False

    def fetch_active_companies(self, retries: int = 3, backoff_factor: float = 1.5) -> list:
        """
        Queries Tally for all loaded/active companies, returning their details (name, guid, company code, token).
        """
        payload = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>CompanyCollection</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVCURRENTCOMPANY>{self.company}</SVCURRENTCOMPANY>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="CompanyCollection">
            <TYPE>Company</TYPE>
            <FETCH>Name, GUID, UserCompanyCode, CmpResTokenRead</FETCH>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""

        url = self.base_url
        logger.info(f"Querying loaded companies from Tally at {url} using custom TDL...")
        
        for attempt in range(1, retries + 1):
            try:
                response = self._post(url, data=payload, timeout=15)
                response.raise_for_status()
                
                content = response.text
                if not content or not content.strip():
                    raise ValueError("Tally returned an empty response.")
                
                # Clean up invalid XML character references or control characters
                import re
                cleaned_xml = re.sub(r'&#x[0-9a-fA-F]+;', '', content)
                cleaned_xml = re.sub(r'&#[0-9]+;', '', cleaned_xml)
                cleaned_xml = re.sub(r'<(/?)UDF:', r'<\1', cleaned_xml, flags=re.IGNORECASE)
                cleaned_xml = "".join(ch for ch in cleaned_xml if ord(ch) >= 32 or ch in "\r\n\t")
                
                import xml.etree.ElementTree as ET
                root = ET.fromstring(cleaned_xml.strip())
                
                companies = []
                for comp_elem in root.findall(".//COMPANY"):
                    comp_name = comp_elem.get('NAME') or (comp_elem.find('NAME').text if comp_elem.find('NAME') is not None else "")
                    if not comp_name:
                        continue
                        
                    guid = comp_elem.find('GUID').text if comp_elem.find('GUID') is not None else ""
                    company_code = comp_elem.find('.//USERCOMPANYCODE').text if comp_elem.find('.//USERCOMPANYCODE') is not None else ""
                    token = comp_elem.find('.//CMPRESTOKENREAD').text if comp_elem.find('.//CMPRESTOKENREAD') is not None else ""
                    
                    companies.append({
                        "name": comp_name.strip(),
                        "number": guid.strip(),
                        "code": company_code.strip(),
                        "token": token.strip()
                    })
                
                return companies
                
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{retries} to fetch active companies failed: {str(e)}")
                if attempt == retries:
                    logger.error("Failed to query active companies from Tally.")
                    raise
                time.sleep(backoff_factor ** attempt)
        return []

