import http.server
import json
import socket
import urllib.parse
from .config import settings
from .logger import setup_logger
import os

logger = setup_logger("web_server", settings.LOG_LEVEL)

class SyncStateMeta(type):
    @property
    def enabled(cls):
        return cls.get_enabled(None)
    @enabled.setter
    def enabled(cls, value):
        cls.set_enabled(None, value)

    @property
    def sync_new(cls):
        return cls.get_sync_new(None)
    @sync_new.setter
    def sync_new(cls, value):
        cls.set_sync_new(None, value)

    @property
    def sync_modified(cls):
        return cls.get_sync_modified(None)
    @sync_modified.setter
    def sync_modified(cls, value):
        cls.set_sync_modified(None, value)

    @property
    def force_reconcile(cls):
        return cls.get_force_reconcile(None)
    @force_reconcile.setter
    def force_reconcile(cls, value):
        cls.set_force_reconcile(None, value)

# Global status tracker
class SyncState(metaclass=SyncStateMeta):
    enabled_map = {}
    sync_new_map = {}
    sync_modified_map = {}
    force_reconcile_map = {}

    last_sync = "Never"
    oracle_status = "Connected"
    tally_status = "Disconnected"
    metrics_cache = None
    metrics_cache_time = 0.0

    @classmethod
    def get_enabled(cls, company_id=None):
        key = str(company_id) if company_id is not None else str(settings.DB_COMPANY_ID)
        return cls.enabled_map.get(key, True if key in ["10", str(settings.DB_COMPANY_ID)] else False)

    @classmethod
    def set_enabled(cls, company_id, val):
        key = str(company_id) if company_id is not None else str(settings.DB_COMPANY_ID)
        cls.enabled_map[key] = val

    @classmethod
    def get_sync_new(cls, company_id=None):
        key = str(company_id) if company_id is not None else str(settings.DB_COMPANY_ID)
        return cls.sync_new_map.get(key, True if key in ["10", str(settings.DB_COMPANY_ID)] else False)

    @classmethod
    def set_sync_new(cls, company_id, val):
        key = str(company_id) if company_id is not None else str(settings.DB_COMPANY_ID)
        cls.sync_new_map[key] = val

    @classmethod
    def get_sync_modified(cls, company_id=None):
        key = str(company_id) if company_id is not None else str(settings.DB_COMPANY_ID)
        return cls.sync_modified_map.get(key, True if key in ["10", str(settings.DB_COMPANY_ID)] else False)

    @classmethod
    def set_sync_modified(cls, company_id, val):
        key = str(company_id) if company_id is not None else str(settings.DB_COMPANY_ID)
        cls.sync_modified_map[key] = val

    @classmethod
    def get_force_reconcile(cls, company_id=None):
        key = str(company_id) if company_id is not None else "all"
        return cls.force_reconcile_map.get(key, False)

    @classmethod
    def set_force_reconcile(cls, company_id, val):
        key = str(company_id) if company_id is not None else "all"
        cls.force_reconcile_map[key] = val


def get_tally_status():
    # Simple check if Tally port is open
    try:
        url_parts = urllib.parse.urlparse(settings.TALLY_URL)
        host = url_parts.hostname or "192.168.64.2"
        port = url_parts.port or 9000
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex((host, port))
        sock.close()
        return "Connected" if result == 0 else "Disconnected"
    except Exception:
        return "Disconnected"

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress standard logging to prevent console clutter
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif path == "/api/companies":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            companies = []
            try:
                from .oracle_client import OracleSyncClient
                client = OracleSyncClient()
                conn = client._get_connection()
                cur = conn.cursor()
                cur.execute(f"""
                    SELECT COMPANY_ID, COMPANY_CODE, COMPANY_NAME 
                    FROM {settings.DB_SCHEMA}.COMPANY_MASTER 
                    WHERE COMPANY_ID IN (11, 12)
                    ORDER BY COMPANY_NAME ASC
                """)
                for row in cur.fetchall():
                    companies.append({
                        "id": row[0],
                        "code": row[1],
                        "name": row[2]
                    })
                cur.close()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to fetch companies: {e}")
            
            self.wfile.write(json.dumps(companies).encode("utf-8"))
        elif path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            company_id = query_params.get("company_id", [None])[0]
            if company_id == "all" or company_id == "null" or company_id == "" or company_id is None:
                company_id = str(settings.DB_COMPANY_ID)
                
            # Fetch recent logs from sync_agent.log if it exists
            recent_logs = []
            try:
                log_path = "logs/sync_agent.log"
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        recent_logs = [line.strip() for line in lines[-150:]]
            except Exception:
                pass

            SyncState.tally_status = get_tally_status()
            
            import time
            current_time = time.time()
            metrics = {"synced": 0, "pending": 0, "new": 0, "error": None}
            
            if not hasattr(SyncState, 'metrics_cache') or not isinstance(SyncState.metrics_cache, dict):
                SyncState.metrics_cache = {}
                SyncState.metrics_cache_time = {}
                
            cache_key = str(company_id) if company_id is not None else "all"
            
            if cache_key in SyncState.metrics_cache and (current_time - SyncState.metrics_cache_time.get(cache_key, 0.0) < 5.0):
                metrics = SyncState.metrics_cache[cache_key]
            else:
                try:
                    from .oracle_client import OracleSyncClient
                    client = OracleSyncClient()
                    conn = client._get_connection()
                    cur = conn.cursor()
                    
                    if company_id is not None:
                        cur.execute(f"""
                            SELECT 
                                SUM(CASE WHEN TALLY_SYNC = 'S' AND UPDATED_BY = 'TALLY_SYNC' THEN 1 ELSE 0 END),
                                SUM(CASE WHEN TALLY_SYNC = 'U' OR TALLY_SYNC = ' ' THEN 1 ELSE 0 END),
                                SUM(CASE WHEN TALLY_SYNC IS NULL THEN 1 ELSE 0 END),
                                SUM(CASE WHEN STUDENT_STATUS = 'L' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ') THEN 1 ELSE 0 END),
                                SUM(CASE WHEN STUDENT_STATUS = 'P' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ') THEN 1 ELSE 0 END),
                                COUNT(1)
                            FROM {settings.DB_SCHEMA}.STUDENT_MASTER_DATA
                            WHERE COMPANY_ID = :company_id
                        """, {"company_id": int(company_id)})
                    else:
                        cur.execute(f"""
                            SELECT 
                                SUM(CASE WHEN TALLY_SYNC = 'S' AND UPDATED_BY = 'TALLY_SYNC' THEN 1 ELSE 0 END),
                                SUM(CASE WHEN TALLY_SYNC = 'U' OR TALLY_SYNC = ' ' THEN 1 ELSE 0 END),
                                SUM(CASE WHEN TALLY_SYNC IS NULL THEN 1 ELSE 0 END),
                                SUM(CASE WHEN STUDENT_STATUS = 'L' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ') THEN 1 ELSE 0 END),
                                SUM(CASE WHEN STUDENT_STATUS = 'P' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ') THEN 1 ELSE 0 END),
                                COUNT(1)
                            FROM {settings.DB_SCHEMA}.STUDENT_MASTER_DATA
                        """)
                    row = cur.fetchone()
                    cur.close()
                    conn.close()
                    
                    metrics["synced"] = row[0] if row[0] is not None else 0
                    metrics["pending"] = row[1] if row[1] is not None else 0
                    metrics["new"] = row[2] if row[2] is not None else 0
                    metrics["left_out"] = row[3] if row[3] is not None else 0
                    metrics["passed_out"] = row[4] if row[4] is not None else 0
                    metrics["total"] = row[5] if row[5] is not None else 0
                    SyncState.oracle_status = "Connected"
                except Exception as e:
                    metrics["error"] = str(e)
                    SyncState.oracle_status = "Disconnected"
                
                SyncState.metrics_cache[cache_key] = metrics
                SyncState.metrics_cache_time[cache_key] = current_time
            
            status = {
                "sync_enabled": SyncState.get_enabled(company_id),
                "sync_new": SyncState.get_sync_new(company_id),
                "sync_modified": SyncState.get_sync_modified(company_id),
                "force_reconcile": SyncState.get_force_reconcile(company_id),
                "tally_status": SyncState.tally_status,
                "oracle_status": SyncState.oracle_status,
                "last_sync": SyncState.last_sync,
                "logs": recent_logs,
                "metrics": metrics
            }
            self.wfile.write(json.dumps(status).encode("utf-8"))
        elif path == "/api/students/list":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            company_id = query_params.get("company_id", [None])[0]
            metric_type = query_params.get("type", [None])[0]
            
            if company_id == "all" or company_id == "null" or company_id == "" or company_id is None:
                company_id = "12"
                
            tally_students_map = {}
            if metric_type in ("pending", "passed_out", "left_out"):
                # First fetch DB students to see how many there are
                db_students_for_count = []
                try:
                    from .oracle_client import OracleSyncClient
                    client = OracleSyncClient()
                    conn = client._get_connection()
                    cur = conn.cursor()
                    
                    where_clause = ""
                    params = {"company_id": int(company_id)}
                    
                    if metric_type == "synced":
                        where_clause = "AND TALLY_SYNC = 'S' AND UPDATED_BY = 'TALLY_SYNC'"
                    elif metric_type == "pending":
                        where_clause = "AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')"
                    elif metric_type == "new":
                        where_clause = "AND TALLY_SYNC IS NULL"
                    elif metric_type == "passed_out":
                        where_clause = "AND STUDENT_STATUS = 'P' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')"
                    elif metric_type == "left_out":
                        where_clause = "AND STUDENT_STATUS = 'L' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')"
                    elif metric_type == "total":
                        where_clause = ""
                        
                    query = f"""
                        SELECT ENRL_NO
                        FROM {settings.DB_SCHEMA}.STUDENT_MASTER_DATA
                        WHERE COMPANY_ID = :company_id {where_clause}
                    """
                    cur.execute(query, params)
                    db_students_for_count = [r[0] for r in cur.fetchall() if r[0]]
                    cur.close()
                    conn.close()
                except Exception as ex:
                    logger.error(f"Error pre-fetching student counts: {ex}")
                
                # Fetch tally details based on count
                if db_students_for_count:
                    from .tally_client import TallyClient
                    tally_client = TallyClient()
                    
                    if len(db_students_for_count) <= 20:
                        logger.info(f"Only {len(db_students_for_count)} records to check. Fetching Tally details individually...")
                        for en in db_students_for_count:
                            try:
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
    <SVOBJECTNAME>{en}</SVOBJECTNAME>
    <SVCURRENTCOMPANY>{tally_client.company}</SVCURRENTCOMPANY>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""
                                import requests
                                from .parser import parse_students_xml
                                response = tally_client._post(tally_client.base_url, data=payload, timeout=5)
                                response.raise_for_status()
                                content = response.text
                                if content and content.strip() and "<LEDGER" in content:
                                    parsed = parse_students_xml(content)
                                    if parsed:
                                        tally_students_map[str(en).strip().lower()] = parsed[0]
                            except Exception as single_ex:
                                logger.warning(f"Error fetching single Tally student {en}: {single_ex}")
                    else:
                        # Fallback to cached bulk load
                        import time
                        current_time = time.time()
                        if hasattr(SyncState, 'tally_cache') and SyncState.tally_cache and (current_time - getattr(SyncState, 'tally_cache_time', 0.0) < 120.0):
                            tally_students_map = SyncState.tally_cache
                            logger.info("Using cached bulk Tally student details (cache hit)")
                        else:
                            try:
                                logger.info("Fetching fresh bulk Tally student details...")
                                from .parser import parse_students_xml
                                xml_data = tally_client.fetch_student_details()
                                tally_list = parse_students_xml(xml_data)
                                tally_students_map = {str(s["enrollment_no"]).strip().lower(): s for s in tally_list if s.get("enrollment_no")}
                                SyncState.tally_cache = tally_students_map
                                SyncState.tally_cache_time = current_time
                            except Exception as ex:
                                logger.warning(f"Could not fetch bulk Tally student details: {ex}")

            students = []
            try:
                from .oracle_client import OracleSyncClient
                client = OracleSyncClient()
                conn = client._get_connection()
                cur = conn.cursor()
                
                where_clause = ""
                params = {"company_id": int(company_id)}
                
                if metric_type == "synced":
                    where_clause = "AND TALLY_SYNC = 'S' AND UPDATED_BY = 'TALLY_SYNC'"
                elif metric_type == "pending":
                    where_clause = "AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')"
                elif metric_type == "new":
                    where_clause = "AND TALLY_SYNC IS NULL"
                elif metric_type == "passed_out":
                    where_clause = "AND STUDENT_STATUS = 'P' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')"
                elif metric_type == "left_out":
                    where_clause = "AND STUDENT_STATUS = 'L' AND (TALLY_SYNC = 'U' OR TALLY_SYNC = ' ')"
                elif metric_type == "total":
                    where_clause = ""
                
                query = f"""
                    SELECT ENRL_NO, STUDENT_NAME, BRANCH, ROLL_NO, COURSE, STUDENT_STATUS, TALLY_SYNC,
                           FATHER_NAME, MOTHER_NAME, STUDENT_GENDER, STUDENT_MOBILE, STUDENT_EMAIL_ID, SESSION_YEAR, REG_NO
                    FROM {settings.DB_SCHEMA}.STUDENT_MASTER_DATA
                    WHERE COMPANY_ID = :company_id {where_clause}
                    ORDER BY STUDENT_NAME ASC
                """
                cur.execute(query, params)
                for row in cur.fetchall():
                    db_rec = {
                        "enrollment_no": row[0] or "",
                        "student_name": row[1] or "Unknown",
                        "branch": row[2] or "",
                        "roll_no": row[3] or "",
                        "course": row[4] or "",
                        "student_status": row[5] or "",
                        "tally_sync": row[6] or "",
                        "father_name": row[7] or "",
                        "mother_name": row[8] or "",
                        "student_gender": row[9] or "",
                        "student_mobile": row[10] or "",
                        "student_email_id": row[11] or "",
                        "session_year": row[12] or "",
                        "reg_no": row[13] or ""
                    }
                    
                    diff_str = ""
                    if metric_type in ("pending", "passed_out", "left_out"):
                        en_key = db_rec["enrollment_no"].strip().lower()
                        tally_rec = tally_students_map.get(en_key)
                        if not tally_rec:
                            for k, v in tally_students_map.items():
                                if k.endswith(f"-{en_key}"):
                                    tally_rec = v
                                    break
                                    
                        if tally_rec:
                            diff_parts = []
                            mapping = [
                                ("student_name", "Name", "student_name"),
                                ("branch", "Branch", "student_class"),
                                ("roll_no", "Roll No", "roll_no"),
                                ("reg_no", "Reg No", "registration_no"),
                                ("course", "Course", "course"),
                                ("session_year", "Session", "session"),
                                ("father_name", "Father Name", "father_name"),
                                ("mother_name", "Mother Name", "mother_name"),
                                ("student_gender", "Gender", "gender"),
                                ("student_mobile", "Mobile", "mobile"),
                                ("student_email_id", "Email", "email")
                            ]
                            for db_f, label, tally_f in mapping:
                                db_val = str(db_rec.get(db_f) or "").strip()
                                tally_val = str(tally_rec.get(tally_f) or "").strip()
                                if db_f == "branch":
                                    from .tally_client import clean_group_name
                                    db_val = clean_group_name(db_val).lower()
                                    tally_val = clean_group_name(tally_val).lower()
                                if db_f == "student_email_id":
                                    db_val = db_val.lower()
                                    tally_val = tally_val.lower()
                                    
                                if db_val != tally_val:
                                    diff_parts.append(f"{label}: '{db_rec.get(db_f) or ''}' vs Tally '{tally_rec.get(tally_f) or ''}'")
                                    
                            db_left = str(db_rec.get("student_status") or "").strip().upper() in ('P', 'L')
                            tally_left = tally_rec.get("is_left", False)
                            if db_left != tally_left:
                                diff_parts.append(f"Status: '{db_rec.get('student_status') or ''}' vs Tally Left: {tally_left}")
                                
                            if diff_parts:
                                diff_str = ", ".join(diff_parts)
                            else:
                                diff_str = "No field diffs found (Triggered by manual flag or alter trigger without value changes)"
                        else:
                            diff_str = "New record (Ledger not found in Tally)"
                            
                    students.append({
                        "enrollment_no": db_rec["enrollment_no"],
                        "name": db_rec["student_name"],
                        "branch": db_rec["branch"],
                        "roll_no": db_rec["roll_no"],
                        "course": db_rec["course"],
                        "status": db_rec["student_status"],
                        "tally_sync": db_rec["tally_sync"],
                        "diff": diff_str
                    })
                cur.close()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to fetch student details: {e}")
                
            self.wfile.write(json.dumps(students).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/toggle":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            success = False
            company_id = None
            try:
                params = json.loads(post_data) if post_data else {}
                switch_type = params.get("switch")
                company_id = params.get("company_id")
                if company_id == "all" or company_id == "null" or company_id == "":
                    company_id = None
                
                if switch_type == "sync_new":
                    val = not SyncState.get_sync_new(company_id)
                    SyncState.set_sync_new(company_id, val)
                    logger.info(f"Sync New Students route toggled for company {company_id}: {'ENABLED' if val else 'DISABLED'}")
                elif switch_type == "sync_modified":
                    val = not SyncState.get_sync_modified(company_id)
                    SyncState.set_sync_modified(company_id, val)
                    logger.info(f"Sync Modifications route toggled for company {company_id}: {'ENABLED' if val else 'DISABLED'}")
                elif switch_type == "force_reconcile":
                    val = not SyncState.get_force_reconcile(company_id)
                    SyncState.set_force_reconcile(company_id, val)
                    logger.info(f"Force Reconcile route toggled for company {company_id}: {'ENABLED' if val else 'DISABLED'}")
                else:
                    val = not SyncState.get_enabled(company_id)
                    SyncState.set_enabled(company_id, val)
                    logger.info(f"Global sync system toggled for company {company_id}: {'ENABLED' if val else 'DISABLED'}")
                
                success = True
            except Exception as e:
                logger.error(f"Error parsing toggle parameters: {e}")
                val = not SyncState.get_enabled(company_id)
                SyncState.set_enabled(company_id, val)
                success = True
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": success,
                "sync_enabled": SyncState.get_enabled(company_id),
                "sync_new": SyncState.get_sync_new(company_id),
                "sync_modified": SyncState.get_sync_modified(company_id),
                "force_reconcile": SyncState.get_force_reconcile(company_id)
            }).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synctal Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #080c14;
            --bg-card: rgba(15, 22, 38, 0.7);
            --border-color: rgba(255, 255, 255, 0.06);
            --accent-primary: #6366f1;
            --accent-secondary: #a855f7;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --info: #06b6d4;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 5% 5%, rgba(99, 102, 241, 0.12) 0%, transparent 35%),
                radial-gradient(circle at 95% 95%, rgba(168, 85, 247, 0.12) 0%, transparent 35%);
        }

        header {
            width: 100%;
            max-width: 1400px;
            padding: 2rem 1.5rem 0.5rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 1.6rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .logo-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent-secondary);
            display: inline-block;
            box-shadow: 0 0 10px var(--accent-secondary);
        }

        .dashboard-layout {
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 1.5rem;
            max-width: 1400px;
            width: 100%;
            padding: 1.5rem;
            margin: 0 auto;
        }

        .sidebar {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 1rem;
            height: fit-content;
        }

        .sidebar-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .company-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-height: 500px;
            overflow-y: auto;
            padding-right: 0.25rem;
        }

        .company-item {
            padding: 0.75rem 1rem;
            border-radius: 10px;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s ease;
            font-size: 0.85rem;
            font-weight: 500;
            color: var(--text-secondary);
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }

        .company-item:hover {
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-primary);
            border-color: rgba(255, 255, 255, 0.05);
        }

        .company-item.active {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15));
            color: var(--text-primary);
            border-color: rgba(99, 102, 241, 0.3);
        }

        .company-code {
            font-size: 0.7rem;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--accent-secondary);
        }

        .main-content {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.2rem;
        }

        @media (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            .dashboard-body {
                grid-template-columns: 1fr !important;
            }
        }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, border-color 0.3s ease;
            cursor: pointer;
        }

        .metric-card:hover {
            transform: translateY(-2px);
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
        }

        .metric-card.synced::before { background-color: var(--success); }
        .metric-card.pending::before { background-color: var(--warning); }
        .metric-card.new::before { background-color: var(--info); }
        .metric-card.passout::before { background-color: var(--accent-secondary); }
        .metric-card.leftout::before { background-color: var(--danger); }

        .metric-card.synced:hover { border-color: rgba(16, 185, 129, 0.3); }
        .metric-card.pending:hover { border-color: rgba(245, 158, 11, 0.3); }
        .metric-card.new:hover { border-color: rgba(6, 182, 212, 0.3); }
        .metric-card.passout:hover { border-color: rgba(168, 85, 247, 0.3); }
        .metric-card.leftout:hover { border-color: rgba(239, 68, 68, 0.3); }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .metric-label {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metric-val {
            font-size: 2.2rem;
            font-weight: 800;
            margin-top: 0.2rem;
        }

        .metric-desc {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .metric-badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            text-transform: uppercase;
        }

        .synced .metric-badge { background-color: rgba(16, 185, 129, 0.1); color: var(--success); }
        .pending .metric-badge { background-color: rgba(245, 158, 11, 0.1); color: var(--warning); }
        .new .metric-badge { background-color: rgba(6, 182, 212, 0.1); color: var(--info); }
        .passout .metric-badge { background-color: rgba(168, 85, 247, 0.1); color: var(--accent-secondary); }
        .leftout .metric-badge { background-color: rgba(239, 68, 68, 0.1); color: var(--danger); }

        /* Dashboard Body Layout */
        .dashboard-body {
            display: grid;
            grid-template-columns: 1fr 1.6fr;
            gap: 1.5rem;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.8rem;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: border-color 0.3s ease;
        }

        .card:hover {
            border-color: rgba(99, 102, 241, 0.2);
        }

        .controls-card {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .section-header {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.015);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.6rem;
        }

        .status-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        .status-val {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.95rem;
            font-weight: 600;
        }

        .pulse {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .pulse.connected {
            background-color: var(--success);
            box-shadow: 0 0 10px var(--success);
            animation: pulse-green 2s infinite;
        }

        .pulse.disconnected {
            background-color: var(--danger);
            box-shadow: 0 0 10px var(--danger);
            animation: pulse-red 2s infinite;
        }

        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
            70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        .toggle-group {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }

        .toggle-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.015);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .toggle-container:hover {
            background: rgba(255, 255, 255, 0.03);
            border-color: rgba(255, 255, 255, 0.1);
        }

        .toggle-info {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }

        .toggle-label {
            font-size: 0.9rem;
            font-weight: 600;
        }

        .toggle-desc {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 46px;
            height: 24px;
            flex-shrink: 0;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255, 255, 255, 0.06);
            transition: .3s;
            border-radius: 24px;
            border: 1px solid var(--border-color);
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 3px;
            bottom: 3px;
            background-color: #ffffff;
            transition: .3s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
        }

        input:checked + .slider:before {
            transform: translateX(22px);
        }

        /* Logs Card */
        .log-card {
            display: flex;
            flex-direction: column;
            height: 600px;
        }

        .log-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 0.8rem;
        }

        .log-tabs {
            display: flex;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            padding: 0.25rem;
            border-radius: 10px;
            gap: 0.2rem;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.4rem 0.9rem;
            border-radius: 8px;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .tab-btn:hover {
            color: var(--text-primary);
        }

        .tab-btn.active {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
        }

        .log-actions {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }

        .search-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.4rem 0.8rem;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.85rem;
            outline: none;
            width: 180px;
            transition: width 0.3s ease, border-color 0.3s ease;
        }

        .search-box:focus {
            width: 220px;
            border-color: rgba(99, 102, 241, 0.5);
        }

        .autoscroll-toggle {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
            cursor: pointer;
            user-select: none;
        }

        .log-console {
            background-color: #0c0f17;
            color: #e5e7eb;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.2rem;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.8rem;
            overflow-y: auto;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            box-shadow: inset 0 0 16px rgba(0, 0, 0, 0.5);
        }

        .log-entry {
            line-height: 1.5;
            border-bottom: 1px solid rgba(255, 255, 255, 0.015);
            padding-bottom: 0.25rem;
            white-space: pre-wrap;
            display: flex;
            gap: 0.5rem;
        }

        .log-time {
            color: #6b7280;
            flex-shrink: 0;
            user-select: none;
        }

        .log-message {
            word-break: break-all;
        }

        /* Log Entry Colors */
        .log-entry.error {
            background-color: rgba(239, 68, 68, 0.08);
            border-left: 2px solid var(--danger);
            padding-left: 0.4rem;
            color: #fca5a5;
        }

        .log-entry.warning {
            background-color: rgba(245, 158, 11, 0.06);
            border-left: 2px solid var(--warning);
            padding-left: 0.4rem;
            color: #fde047;
        }

        .log-entry.info {
            color: #93c5fd;
        }

        .log-entry.success {
            color: #86efac;
            font-weight: 500;
        }

        .log-entry.debug {
            color: #9ca3af;
        }

        /* Modal styling */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(8px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            padding: 1rem;
            animation: fadeIn 0.2s ease-out;
        }

        .modal-container {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            width: 100%;
            max-width: 900px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .modal-close:hover {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }

        body.light-theme .modal-close:hover {
            background: rgba(0, 0, 0, 0.05);
        }

        .modal-search-bar {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .modal-search-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.6rem 1rem;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .modal-search-input:focus {
            border-color: var(--accent-primary);
        }

        body.light-theme .modal-search-input {
            background: rgba(0, 0, 0, 0.02);
        }

        .modal-body {
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
        }

        .student-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            text-align: left;
        }

        .student-table th {
            padding: 0.75rem 1rem;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }

        .student-table td {
            padding: 0.85rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            color: var(--text-primary);
        }

        body.light-theme .student-table td {
            border-bottom: 1px solid rgba(0, 0, 0, 0.03);
        }

        .student-table tr:hover {
            background: rgba(255, 255, 255, 0.01);
        }

        body.light-theme .student-table tr:hover {
            background: rgba(0, 0, 0, 0.01);
        }

        .badge-status {
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
        }

        .badge-status.S { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        .badge-status.U { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
        .badge-status.none { background: rgba(6, 182, 212, 0.1); color: var(--info); }

        .modal-empty {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* Light Theme Variable Overrides */
        body.light-theme {
            --bg-primary: #f4f6fa;
            --bg-card: rgba(255, 255, 255, 0.9);
            --border-color: rgba(0, 0, 0, 0.08);
            --text-primary: #1f2937;
            --text-secondary: #4b5563;
            background-image: 
                radial-gradient(circle at 5% 5%, rgba(99, 102, 241, 0.05) 0%, transparent 35%),
                radial-gradient(circle at 95% 95%, rgba(168, 85, 247, 0.05) 0%, transparent 35%);
        }

        .theme-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.2s ease;
        }
        .theme-btn:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        body.light-theme .theme-btn {
            background: rgba(0, 0, 0, 0.04);
        }
        body.light-theme .theme-btn:hover {
            background: rgba(0, 0, 0, 0.08);
        }
        body.light-theme .company-item:hover {
            background: rgba(0, 0, 0, 0.02);
            border-color: rgba(0, 0, 0, 0.05);
        }
        body.light-theme .status-item,
        body.light-theme .toggle-container {
            background: rgba(0, 0, 0, 0.015);
        }
        body.light-theme .tab-btn {
            color: var(--text-secondary);
        }
        body.light-theme .tab-btn.active {
            background: rgba(0, 0, 0, 0.06);
            color: var(--text-primary);
        }
        body.light-theme .search-box {
            background: rgba(0, 0, 0, 0.02);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <span class="logo-dot"></span>
            ELOGITRIAL'S CONTROL CENTER
        </div>
        <button id="theme-toggle" class="theme-btn">☀️ Light Mode</button>
    </header>
    <div class="dashboard-layout">
        <!-- Left Sidebar: Company Selector -->
        <aside class="sidebar">
            <div class="sidebar-title">Companies</div>
            <div class="company-list" id="company-list">
            </div>
        </aside>

        <!-- Right Main Content -->
        <main class="main-content">
            <!-- Top Metrics Cards -->
            <div class="metrics-grid">
                <div class="metric-card synced" onclick="openMetricModal('synced', 'Synced Records')">
                    <div class="metric-header">
                        <span class="metric-label">Synced Records</span>
                        <span class="metric-badge">Status 'S'</span>
                    </div>
                    <div class="metric-val" id="metric-synced">0</div>
                    <div class="metric-desc">Ledgers match & updated in Tally</div>
                </div>
                
                <div class="metric-card pending" onclick="openMetricModal('pending', 'Pending Sync Records')">
                    <div class="metric-header">
                        <span class="metric-label">Pending Sync</span>
                        <span class="metric-badge">Status 'U'</span>
                    </div>
                    <div class="metric-val" id="metric-pending">0</div>
                    <div class="metric-desc">Modified records awaiting retry/push</div>
                </div>
                
                <div class="metric-card new" onclick="openMetricModal('new', 'New Records (Never Synced)')">
                    <div class="metric-header">
                        <span class="metric-label">New Records</span>
                        <span class="metric-badge">Status 'NULL'</span>
                    </div>
                    <div class="metric-val" id="metric-new">0</div>
                    <div class="metric-desc">Never synced to Tally database</div>
                </div>

                <div class="metric-card new" style="border-left: 4px solid var(--accent-primary);" onclick="openMetricModal('total', 'Total Students')">
                    <div class="metric-header">
                        <span class="metric-label">Total Students</span>
                        <span class="metric-badge" style="background-color: rgba(99, 102, 241, 0.1); color: var(--accent-primary);">Total</span>
                    </div>
                    <div class="metric-val" id="metric-total">0</div>
                    <div class="metric-desc">Total records in database</div>
                </div>

                <div class="metric-card passout" onclick="openMetricModal('passed_out', 'Pending Passed Out Records')">
                    <div class="metric-header">
                        <span class="metric-label">Pending Passed Out</span>
                        <span class="metric-badge">Status 'P' & 'U'</span>
                    </div>
                    <div class="metric-val" id="metric-passout">0</div>
                    <div class="metric-desc">Remaining passed out to sync</div>
                </div>

                <div class="metric-card leftout" onclick="openMetricModal('left_out', 'Pending Left Out Records')">
                    <div class="metric-header">
                        <span class="metric-label">Pending Left Out</span>
                        <span class="metric-badge">Status 'L' & 'U'</span>
                    </div>
                    <div class="metric-val" id="metric-leftout">0</div>
                    <div class="metric-desc">Remaining left out to sync</div>
                </div>
            </div>

            <!-- Dashboard Body -->
            <div class="dashboard-body">
                <!-- Left Controls Column -->
                <div class="card controls-card">
                    <div>
                        <div class="section-header">
                            <span>Connection Status</span>
                        </div>
                        
                        <div class="status-item">
                            <span class="status-label">Oracle Database</span>
                            <div class="status-val" id="oracle-indicator">
                                <span class="pulse disconnected" id="oracle-pulse"></span>
                                <span id="oracle-text">Checking...</span>
                            </div>
                        </div>

                        <div class="status-item">
                            <span class="status-label">Tally Prime Port</span>
                            <div class="status-val" id="tally-indicator">
                                <span class="pulse disconnected" id="tally-pulse"></span>
                                <span id="tally-text">Checking...</span>
                            </div>
                        </div>
                        
                        <div class="status-item">
                            <span class="status-label">Last Sync Cycle</span>
                            <div class="status-val" style="color: var(--text-primary);" id="last-sync-time">
                                Never
                            </div>
                        </div>
                    </div>

                    <div>
                        <div class="section-header">
                            <span>Sync Control Center</span>
                        </div>
                        
                        <div class="toggle-group">
                            <!-- Toggle 1: Global Automatic Sync -->
                            <div class="toggle-container">
                                <div class="toggle-info">
                                    <span class="toggle-label">Global Active Sync</span>
                                    <span class="toggle-desc">Enable background polling cycles</span>
                                </div>
                                <label class="switch">
                                    <input type="checkbox" id="sync-switch" checked onchange="toggleSync('global')">
                                    <span class="slider"></span>
                                </label>
                            </div>

                            <!-- Toggle 2: Route 1 - Sync New Students -->
                            <div class="toggle-container">
                                <div class="toggle-info">
                                    <span class="toggle-label">Sync New Students</span>
                                    <span class="toggle-desc">Create missing student ledgers</span>
                                </div>
                                <label class="switch">
                                    <input type="checkbox" id="sync-new-switch" checked onchange="toggleSync('sync_new')">
                                    <span class="slider"></span>
                                </label>
                            </div>

                            <!-- Toggle 3: Route 2 - Sync modifications & details -->
                            <div class="toggle-container">
                                <div class="toggle-info">
                                    <span class="toggle-label">Sync Edits/Alterations</span>
                                    <span class="toggle-desc">Instantly push modifications</span>
                                </div>
                                <label class="switch">
                                    <input type="checkbox" id="sync-mod-switch" checked onchange="toggleSync('sync_modified')">
                                    <span class="slider"></span>
                                </label>
                            </div>

                            <!-- Toggle 4: Route 3 - Force Overwrite & Reconcile -->
                            <div class="toggle-container" style="border-color: rgba(245, 158, 11, 0.25);">
                                <div class="toggle-info">
                                    <span class="toggle-label" style="color: var(--warning);">Force Fix All Details</span>
                                    <span class="toggle-desc">Overwrite existing ledger variables</span>
                                </div>
                                <label class="switch">
                                    <input type="checkbox" id="sync-force-switch" onchange="toggleSync('force_reconcile')">
                                    <span class="slider"></span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Logs Column -->
                <div class="card log-card">
                    <div class="log-controls">
                        <div class="log-tabs">
                            <button class="tab-btn active" onclick="setLogTab('all')">ALL</button>
                            <button class="tab-btn" onclick="setLogTab('info')">INFO</button>
                            <button class="tab-btn" onclick="setLogTab('warning')">WARN</button>
                            <button class="tab-btn" onclick="setLogTab('error')">ERROR</button>
                        </div>
                        <div class="log-actions">
                            <input type="text" class="search-box" id="log-search" placeholder="Search logs..." oninput="handleSearch()">
                            <label class="autoscroll-toggle">
                                <input type="checkbox" id="autoscroll" checked> Auto Scroll
                            </label>
                        </div>
                    </div>
                    <div class="log-console" id="log-console">
                        <div class="log-entry">Connecting to background sync service stream...</div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Student List Modal -->
    <div id="student-modal" class="modal-overlay" onclick="closeStudentModalOnOverlay(event)">
        <div class="modal-container">
            <div class="modal-header">
                <h3 class="modal-title" id="modal-title">Student Records</h3>
                <button class="modal-close" onclick="closeStudentModal()">&times;</button>
            </div>
            <div class="modal-search-bar">
                <input type="text" id="modal-search" class="modal-search-input" placeholder="Search by name, roll no, or enrollment..." oninput="filterStudents()">
            </div>
            <div class="modal-body">
                <table class="student-table" id="student-table" style="display: none;">
                    <thead>
                        <tr>
                            <th>Enrollment No</th>
                            <th>Name</th>
                            <th>Branch</th>
                            <th>Roll No</th>
                            <th>Course</th>
                            <th>Status</th>
                            <th>Sync Status</th>
                        </tr>
                    </thead>
                    <tbody id="student-table-body">
                    </tbody>
                </table>
                <div id="modal-loading" class="modal-empty">Loading records...</div>
                <div id="modal-empty-msg" class="modal-empty" style="display: none;">No records found matching status.</div>
            </div>
        </div>
    </div>

    <script>
        let modalStudents = [];

        async function openMetricModal(type, title) {
            const modal = document.getElementById('student-modal');
            const titleEl = document.getElementById('modal-title');
            const table = document.getElementById('student-table');
            const tableBody = document.getElementById('student-table-body');
            const loading = document.getElementById('modal-loading');
            const emptyMsg = document.getElementById('modal-empty-msg');
            const searchInput = document.getElementById('modal-search');

            titleEl.innerText = title;
            searchInput.value = '';
            table.style.display = 'none';
            emptyMsg.style.display = 'none';
            loading.style.display = 'block';
            modal.style.display = 'flex';
            
            modalStudents = [];
            tableBody.innerHTML = '';

            try {
                const url = `/api/students/list?company_id=${selectedCompanyId}&type=${type}`;
                const res = await fetch(url);
                modalStudents = await res.json();
                
                renderModalStudents(modalStudents);
            } catch (err) {
                console.error("Failed to fetch metric students:", err);
                loading.style.display = 'none';
                emptyMsg.innerText = "Error loading student records.";
                emptyMsg.style.display = 'block';
            }
        }

        function renderModalStudents(studentsList) {
            const table = document.getElementById('student-table');
            const tableBody = document.getElementById('student-table-body');
            const loading = document.getElementById('modal-loading');
            const emptyMsg = document.getElementById('modal-empty-msg');

            loading.style.display = 'none';
            tableBody.innerHTML = '';

            if (!studentsList || studentsList.length === 0) {
                table.style.display = 'none';
                emptyMsg.innerText = "No student records found.";
                emptyMsg.style.display = 'block';
                return;
            }

            // Check if any student has a diff field
            const hasDiff = studentsList.some(s => s.diff !== undefined && s.diff !== "");
            
            // Update table headers
            const thead = table.querySelector('thead tr');
            if (hasDiff) {
                thead.innerHTML = `
                    <th>Enrollment No</th>
                    <th>Name</th>
                    <th>Branch</th>
                    <th>Roll No</th>
                    <th>Course</th>
                    <th>Status</th>
                    <th>Sync Status</th>
                    <th>Changes/Differences</th>
                `;
            } else {
                thead.innerHTML = `
                    <th>Enrollment No</th>
                    <th>Name</th>
                    <th>Branch</th>
                    <th>Roll No</th>
                    <th>Course</th>
                    <th>Status</th>
                    <th>Sync Status</th>
                `;
            }

            studentsList.forEach(student => {
                const tr = document.createElement('tr');
                
                const syncVal = student.tally_sync ? student.tally_sync : 'none';
                let syncBadgeClass = 'none';
                if (student.tally_sync === 'S') syncBadgeClass = 'S';
                else if (student.tally_sync === 'U') syncBadgeClass = 'U';
                
                let diffTd = '';
                if (hasDiff) {
                    const diffText = student.diff || '<span style="color: var(--text-secondary); font-style: italic;">No difference</span>';
                    diffTd = `<td style="color: var(--warning); font-size: 0.8rem; max-width: 250px; overflow-wrap: break-word;">${diffText}</td>`;
                }

                tr.innerHTML = `
                    <td style="font-weight: 600;">${student.enrollment_no}</td>
                    <td>${student.name}</td>
                    <td>${student.branch}</td>
                    <td>${student.roll_no}</td>
                    <td>${student.course}</td>
                    <td>${student.status || ''}</td>
                    <td><span class="badge-status ${syncBadgeClass}">${syncVal}</span></td>
                    ${diffTd}
                `;
                tableBody.appendChild(tr);
            });

            table.style.display = 'table';
            emptyMsg.style.display = 'none';
        }

        function filterStudents() {
            const query = document.getElementById('modal-search').value.toLowerCase();
            if (!query) {
                renderModalStudents(modalStudents);
                return;
            }

            const filtered = modalStudents.filter(s => 
                (s.enrollment_no && s.enrollment_no.toLowerCase().includes(query)) ||
                (s.name && s.name.toLowerCase().includes(query)) ||
                (s.roll_no && s.roll_no.toLowerCase().includes(query)) ||
                (s.branch && s.branch.toLowerCase().includes(query)) ||
                (s.course && s.course.toLowerCase().includes(query))
            );

            renderModalStudents(filtered);
        }

        function closeStudentModal() {
            document.getElementById('student-modal').style.display = 'none';
        }

        function closeStudentModalOnOverlay(event) {
            if (event.target === document.getElementById('student-modal')) {
                closeStudentModal();
            }
        }

        // Close on ESC key
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeStudentModal();
            }
        });

        let currentTab = 'all';
        let searchQuery = '';
        let cachedLogs = [];
        let selectedCompanyId = null;

        async function fetchCompanies() {
            try {
                const res = await fetch('/api/companies');
                const companies = await res.json();
                const listEl = document.getElementById('company-list');
                
                listEl.innerHTML = ``;
                
                if (companies.length > 0 && selectedCompanyId === null) {
                    selectedCompanyId = String(companies[0].id);
                }
                
                companies.forEach(company => {
                    const item = document.createElement('div');
                    item.className = `company-item ${selectedCompanyId === String(company.id) ? 'active' : ''}`;
                    item.id = `company-${company.id}`;
                    item.onclick = () => selectCompany(company.id);
                    
                    item.innerHTML = `
                        <span class="company-code">${company.code || 'COMP'}</span>
                        <span>${company.name}</span>
                    `;
                    listEl.appendChild(item);
                });
            } catch (err) {
                console.error("Failed to fetch companies:", err);
            }
        }

        function selectCompany(companyId) {
            selectedCompanyId = companyId !== null ? String(companyId) : null;
            
            const items = document.querySelectorAll('.company-item');
            items.forEach(item => {
                if (item.id === `company-${companyId || 'all'}`) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
            
            fetchStatus();
        }

        async function fetchStatus() {
            try {
                const url = selectedCompanyId ? `/api/status?company_id=${selectedCompanyId}` : '/api/status';
                const res = await fetch(url);
                const data = await res.json();
                
                // Update switch statuses
                document.getElementById('sync-switch').checked = data.sync_enabled;
                document.getElementById('sync-new-switch').checked = data.sync_new;
                document.getElementById('sync-mod-switch').checked = data.sync_modified;
                document.getElementById('sync-force-switch').checked = data.force_reconcile;
                
                // Update tally indicator
                const tallyPulse = document.getElementById('tally-pulse');
                const tallyText = document.getElementById('tally-text');
                if (data.tally_status === 'Connected') {
                    tallyPulse.className = 'pulse connected';
                    tallyText.innerText = 'Connected';
                } else {
                    tallyPulse.className = 'pulse disconnected';
                    tallyText.innerText = 'Offline';
                }

                // Update oracle indicator
                const oraclePulse = document.getElementById('oracle-pulse');
                const oracleText = document.getElementById('oracle-text');
                if (data.oracle_status === 'Connected') {
                    oraclePulse.className = 'pulse connected';
                    oracleText.innerText = 'Connected';
                } else {
                    oraclePulse.className = 'pulse disconnected';
                    oracleText.innerText = 'Offline';
                }
                
                // Update last sync time
                document.getElementById('last-sync-time').innerText = data.last_sync;

                // Update metrics
                if (data.metrics) {
                    document.getElementById('metric-synced').innerText = data.metrics.synced.toLocaleString();
                    document.getElementById('metric-pending').innerText = data.metrics.pending.toLocaleString();
                    document.getElementById('metric-new').innerText = data.metrics.new.toLocaleString();
                    document.getElementById('metric-passout').innerText = (data.metrics.passed_out || 0).toLocaleString();
                    document.getElementById('metric-leftout').innerText = (data.metrics.left_out || 0).toLocaleString();
                    document.getElementById('metric-total').innerText = (data.metrics.total || 0).toLocaleString();
                }
                
                // Update logs
                if (data.logs && data.logs.length > 0) {
                    cachedLogs = data.logs;
                    renderLogs();
                }
            } catch (err) {
                console.error("Failed to fetch status:", err);
            }
        }

        function setLogTab(tab) {
            currentTab = tab;
            // Update active state in UI tabs
            const btns = document.querySelectorAll('.tab-btn');
            btns.forEach(btn => {
                if (btn.innerText.toLowerCase().startsWith(tab)) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            renderLogs();
        }

        function handleSearch() {
            searchQuery = document.getElementById('log-search').value.toLowerCase();
            renderLogs();
        }

        function renderLogs() {
            const consoleEl = document.getElementById('log-console');
            consoleEl.innerHTML = '';
            
            cachedLogs.forEach(log => {
                try {
                    // Parse log entry format: "2026-05-30 14:12:34,076 - oracle_client - INFO - [oracle_client.py:257] - Updated..."
                    let logClass = 'info';
                    let logText = log;
                    let logTime = '';
                    
                    // Try to extract timestamp and level
                    const match = log.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\,\d+)?)\s+-\s+(\w+)\s+-\s+(\w+)/);
                    if (match) {
                        logTime = match[1];
                        const level = match[3].toLowerCase();
                        const remainder = log.substring(match[0].length).replace(/^\s*-\s*\[[^\]]+\]\s*-\s*/, '');
                        logText = remainder;
                        
                        if (level === 'error' || level === 'critical') logClass = 'error';
                        else if (level === 'warning' || level === 'warn') logClass = 'warning';
                        else if (level === 'info') {
                            // Check if it's a success indicator message
                            if (logText.toLowerCase().includes('success') || logText.toLowerCase().includes('synchronized') || logText.includes("TALLY_SYNC set to 'S'")) {
                                logClass = 'success';
                            } else {
                                logClass = 'info';
                            }
                        } else if (level === 'debug') logClass = 'debug';
                    }

                    // Filter by Tab
                    if (currentTab === 'info' && logClass !== 'info' && logClass !== 'success') return;
                    if (currentTab === 'warning' && logClass !== 'warning') return;
                    if (currentTab === 'error' && logClass !== 'error') return;

                    // Filter by Search Query
                    if (searchQuery && !log.toLowerCase().includes(searchQuery)) return;

                    const entry = document.createElement('div');
                    entry.className = `log-entry ${logClass}`;
                    
                    if (logTime) {
                        const timeSpan = document.createElement('span');
                        timeSpan.className = 'log-time';
                        timeSpan.innerText = `[${logTime.split(' ')[1]}]`;
                        entry.appendChild(timeSpan);
                    }

                    const msgSpan = document.createElement('span');
                    msgSpan.className = 'log-message';
                    msgSpan.innerText = logText;
                    entry.appendChild(msgSpan);
                    
                    consoleEl.appendChild(entry);
                } catch (e) {
                    console.error("Error parsing log line:", e, log);
                    // Fallback to simple render
                    const entry = document.createElement('div');
                    entry.className = 'log-entry info';
                    const msgSpan = document.createElement('span');
                    msgSpan.className = 'log-message';
                    msgSpan.innerText = log;
                    entry.appendChild(msgSpan);
                    consoleEl.appendChild(entry);
                }
            });

            // Scroll to bottom if autoscroll is checked
            if (document.getElementById('autoscroll').checked) {
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
        }

        async function toggleSync(type) {
            try {
                const res = await fetch('/api/toggle', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ switch: type, company_id: selectedCompanyId })
                });
                const data = await res.json();
                
                document.getElementById('sync-switch').checked = data.sync_enabled;
                document.getElementById('sync-new-switch').checked = data.sync_new;
                document.getElementById('sync-mod-switch').checked = data.sync_modified;
                document.getElementById('sync-force-switch').checked = data.force_reconcile;
            } catch (err) {
                console.error("Failed to toggle sync:", err);
            }
        }

        // Initialize and poll
        fetchCompanies();
        setInterval(fetchStatus, 2000);
        fetchStatus();

        // Theme Toggle Javascript Logic
        const themeBtn = document.getElementById('theme-toggle');
        const bodyEl = document.body;

        if (localStorage.getItem('theme') === 'light') {
            bodyEl.classList.add('light-theme');
            themeBtn.innerHTML = '🌙 Dark Mode';
        }

        themeBtn.addEventListener('click', () => {
            if (bodyEl.classList.contains('light-theme')) {
                bodyEl.classList.remove('light-theme');
                themeBtn.innerHTML = '☀️ Light Mode';
                localStorage.setItem('theme', 'dark');
            } else {
                bodyEl.classList.add('light-theme');
                themeBtn.innerHTML = '🌙 Dark Mode';
                localStorage.setItem('theme', 'light');
            }
        });
    </script>
</body>
</html>
"""

def start_server(port=8080):
    server = http.server.HTTPServer(("0.0.0.0", port), DashboardHandler)
    logger.info(f"Control dashboard server started on http://localhost:{port}")
    server.serve_forever()

if __name__ == '__main__':
    start_server()
