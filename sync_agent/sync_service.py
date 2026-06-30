from .tally_client import TallyClient
from .parser import parse_students_xml, parse_transactions_xml
from .supabase_client import SupabaseSyncClient
from .oracle_client import OracleSyncClient
from .config import settings
from .logger import setup_logger
import traceback
import asyncio
from supabase import acreate_client

logger = setup_logger("sync_service", settings.LOG_LEVEL)

class SyncService:
    def __init__(self):
        """
        Initializes orchestration layer services.
        """
        self.tally_client = TallyClient()
        self.supabase_client = None
        self.oracle_client = None
        self.is_syncing = False
        self.last_tx_mtime = 0.0
        
        # Load last known sync state of is_left for bidirectional reconciliation
        import os
        import json
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.state_file = os.path.join(base_dir, "logs", "sync_state.json")
        self.sync_state = {}
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.sync_state = json.load(f)
            except Exception:
                pass
                
    def save_sync_state(self):
        import json
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.sync_state, f)
        except Exception as e:
            logger.error(f"Error saving sync state: {e}")

    def _init_oracle(self) -> bool:
        """
        Initializes Oracle DB client lazily.
        """
        if self.oracle_client:
            return True
        try:
            self.oracle_client = OracleSyncClient()
            return True
        except Exception as e:
            logger.error(f"Failed to connect with Oracle Database: {str(e)}")
            return False
        
    def _init_supabase(self) -> bool:
        """
        Initializes Supabase connection lazily to ensure robust daemon boots
        even when database connection is down.
        """
        if not settings.USE_SUPABASE:
            return False
        if self.supabase_client:
            return True
            
        try:
            self.supabase_client = SupabaseSyncClient()
            return True
        except Exception as e:
            logger.error(f"Failed to connect with Supabase integration endpoint: {str(e)}")
            return False


    def _check_numeric_diff(self, val1, val2) -> bool:
        try:
            return abs(float(val1 or 0) - float(val2 or 0)) > 0.01
        except (ValueError, TypeError):
            return str(val1) != str(val2)

    def _datetimes_differ(self, dt_str1: str, dt_str2: str) -> bool:
        if not dt_str1 or not dt_str2:
            return dt_str1 != dt_str2
        try:
            from datetime import datetime, timezone
            # Convert Z to standard timezone offset format if present
            d1_clean = dt_str1.replace('Z', '+00:00')
            d2_clean = dt_str2.replace('Z', '+00:00')
            
            dt1 = datetime.fromisoformat(d1_clean)
            dt2 = datetime.fromisoformat(d2_clean)
            
            if dt1.tzinfo is None:
                dt1 = dt1.replace(tzinfo=timezone.utc)
            if dt2.tzinfo is None:
                dt2 = dt2.replace(tzinfo=timezone.utc)
                
            dt1_utc = dt1.astimezone(timezone.utc)
            dt2_utc = dt2.astimezone(timezone.utc)
            
            # Compare down to minute-level accuracy because Tally doesn't export seconds
            return abs((dt1_utc - dt2_utc).total_seconds()) >= 60
        except Exception:
            return dt_str1.strip() != dt_str2.strip()

    def _records_differ(self, tally_rec: dict, db_rec: dict) -> bool:
        fields_to_compare = [
            "student_name", "student_class", "roll_no", "registration_no", "course",
            "semester", "session", "year", "father_name", "mother_name", "quota",
            "gender", "dob", "blood_group", "mobile", "category", "subcategory",
            "email", "billwise", "admission_category", "seer_no", "rank", "religion",
            "caste", "annual_income", "status", "substatus", "opening_balance",
            "closing_balance", "permanent_address", "permanent_pin", "correspondence_address",
            "correspondence_pin", "created_by", "created_time", "remarks", "admission_mode",
            "is_left"
        ]
        for field in fields_to_compare:
            val1 = tally_rec.get(field)
            val2 = db_rec.get(field)
            
            if field in ("opening_balance", "closing_balance", "annual_income"):
                if self._check_numeric_diff(val1, val2):
                    return True
            elif field in ("billwise", "is_left"):
                if bool(val1) != bool(val2):
                    return True
            elif field == "student_class":
                from .tally_client import clean_group_name
                s1 = clean_group_name(str(val1 or ""))
                s2 = clean_group_name(str(val2 or ""))
                if s1.lower() != s2.lower():
                    return True
            elif field == "email":
                s1 = str(val1 or "").strip().lower()
                s2 = str(val2 or "").strip().lower()
                if s1 != s2:
                    return True
            elif field in ("permanent_address", "correspondence_address"):
                s1 = re.sub(r'\s+', ' ', str(val1 or "")).strip().lower()
                s2 = re.sub(r'\s+', ' ', str(val2 or "")).strip().lower()
                if s1 != s2:
                    return True
            elif field == "created_time":
                s1 = str(val1 or "").strip()
                s2 = str(val2 or "").strip()
                if self._datetimes_differ(s1, s2):
                    return True
            else:
                s1 = str(val1 or "").strip()
                s2 = str(val2 or "").strip()
                if s1 != s2:
                    return True
        return False

    def validate_active_company(self) -> bool:
        """
        Pre-flight check: Validates that the expected company name, code/ID,
        and token match the active company loaded in Tally.
        """
        logger.info("Performing pre-flight Tally company security validation...")
        
        # 1. Fetch expected details from DB (if Oracle is used)
        expected_name = settings.TALLY_COMPANY
        expected_token = None
        expected_code = str(settings.DB_COMPANY_ID)
        
        if settings.USE_ORACLE:
            if not self._init_oracle():
                logger.error("Validation failed: Oracle DB connection missing.")
                return False
            try:
                conn = self.oracle_client._get_connection()
                cur = conn.cursor()
                cur.execute(
                    f"SELECT COMPANY_NAME, TOKEN_ID, COMPANY_CODE FROM {settings.DB_SCHEMA}.COMPANY_MASTER WHERE COMPANY_ID = :1",
                    [settings.DB_COMPANY_ID]
                )
                row = cur.fetchone()
                if row:
                    expected_name = row[0] or expected_name
                    expected_token = row[1]
                    expected_code = row[2] or expected_code
                cur.close()
            except Exception as db_err:
                logger.warning(f"Could not retrieve expected company details from DB: {str(db_err)}. Using settings fallback.")

        # 2. Fetch loaded companies from Tally
        try:
            active_companies = self.tally_client.fetch_active_companies()
        except Exception as tally_err:
            logger.error(f"Validation failed: Unable to connect or query active companies from Tally: {str(tally_err)}")
            return False

        if not active_companies:
            logger.error("Validation failed: No active companies returned from Tally.")
            return False

        # 3. Look for the target company matching expected_name
        target_company = None
        for cmp in active_companies:
            if cmp["name"].strip().lower() == expected_name.strip().lower():
                target_company = cmp
                break

        if not target_company:
            logger.error(
                f"Validation failed: Target company '{expected_name}' is not open/loaded in Tally. "
                f"Currently open: {[c['name'] for c in active_companies]}"
            )
            return False

        # 4. Validate Company Code and Token ID
        tally_code = str(target_company.get("code") or "").strip()
        expected_db_id = str(settings.DB_COMPANY_ID).strip()
        
        if tally_code != expected_db_id and tally_code != str(expected_code).strip():
            logger.error(
                f"Validation failed: Company Code mismatch! "
                f"Tally shows '{tally_code}', DB expects '{expected_db_id}'"
            )
            return False

        if expected_token:
            tally_token = str(target_company.get("token") or "").strip()
            db_token = str(expected_token).strip()
            if tally_token != db_token:
                logger.error("Validation failed: Security Token Mismatch! Integration aborted to prevent data corruption.")
                return False

        logger.info(
            f"Tally company validation SUCCESS for '{expected_name}' (ID: {expected_db_id}, "
            f"Folder No: {target_company.get('number')})."
        )
        return True

    def run_sync_cycle(self, force_job_id: str = None) -> bool:
        """
        Runs one iteration cycle of the student data sync routine.
        """
        from .web_server import SyncState, get_tally_status
        if not SyncState.enabled:
            logger.info("Sync is currently disabled from control dashboard. Skipping cycle.")
            return False
            
        t_status = get_tally_status()
        if t_status == "Disconnected":
            logger.warning("Tally Prime is offline / closed. Pausing sync cycle.")
            return False
            
        logger.info("Executing sync cycle transaction...")
        self.is_syncing = True
        try:
            # 1. Initialize client
            if settings.USE_SUPABASE:
                if not self._init_supabase():
                    logger.error("Supabase connection missing. Aborting sync cycle.")
                    return False
            if settings.USE_ORACLE:
                if not self._init_oracle():
                    logger.error("Oracle DB connection missing. Aborting sync cycle.")
                    return False
                
            # Perform Tally Active Company validation check
            if not self.validate_active_company():
                logger.error("Tally active company validation failed. Skipping sync cycle to protect data integrity.")
                return False

                
            job_id = force_job_id
            try:
                # 2. Start database sync job record if Supabase is used
                if settings.USE_SUPABASE:
                    if not job_id:
                        pending_id = self.supabase_client.get_pending_sync_job()
                        if pending_id:
                            logger.info(f"Detected remote PENDING trigger. Claiming Job: {pending_id}")
                            self.supabase_client.claim_sync_job(pending_id)
                            job_id = pending_id
                        else:
                            job_id = self.supabase_client.start_sync_job()
                    else:
                        self.supabase_client.claim_sync_job(job_id)
                    
                students_list = []
                total_count = 0
                db_map = {}
                tally_ledger_parents = {}
                to_upsert_to_db = []
                processed = 0
                failed = 0

                if not settings.DISABLE_TALLY_TO_DB:
                    # 3. Retrieve XML from Tally Local API
                    logger.info("Sending student details query request to local Tally API gateway...")
                    xml_data = self.tally_client.fetch_student_details()
                    
                    # 4. Parse payload
                    logger.info("Parsing retrieved XML DOM tree to extract student records...")
                    students_list = parse_students_xml(xml_data)
                    
                    total_count = len(students_list)
                    
                    # 5. Fetch all current student records for delta sync
                    logger.info("Fetching current student records from database...")
                    if settings.USE_SUPABASE:
                        res = self.supabase_client.client.table("students").select("*").execute()
                        db_students = res.data or []
                    elif settings.USE_ORACLE:
                        db_students = self.oracle_client.get_all_students()
                    else:
                        db_students = []

                    # Old pre-create course groups block removed from here for optimization (moved to DB -> Tally sync route)
                    
                    # Map DB students by cleaned enrollment_no to handle potential whitespace/newline discrepancies
                    db_map = {str(row["enrollment_no"]).strip(): row for row in db_students if row.get("enrollment_no")}
                    
                    # Fetch ledger parent mappings to detect group changes (especially Left 2026)
                    try:
                        tally_ledger_parents = self.tally_client.fetch_all_ledgers_with_parent()
                    except Exception as e:
                        logger.warning(f"Could not fetch ledger parent mappings: {e}")
                        tally_ledger_parents = {}

                    # A. Tally -> DB Sync (Delta check)
                    for s in students_list:
                        en = s.get("enrollment_no")
                        if not en:
                            continue
                        clean_en = str(en).strip()
                        clean_en_lower = clean_en.lower()
                        
                        student_name = s.get("student_name") or ""
                        expected_ledger_name = f"{student_name.strip()} -{clean_en}".lower() if student_name else clean_en_lower
                        
                        parent_group = tally_ledger_parents.get(clean_en_lower) or tally_ledger_parents.get(expected_ledger_name)
                        
                        tally_left = bool(parent_group and (parent_group.startswith("Left") or parent_group.startswith("Passout")))
                        
                        db_rec = db_map.get(clean_en)
                        if db_rec:
                            db_left = db_rec.get("is_left") in (True, "true", "True", "yes", "Yes", 1, "1")
                        else:
                            db_left = False
                            
                        last_left = self.sync_state.get(clean_en, False)
                        
                        # Resolve state
                        resolved_left = db_left
                        if db_left != last_left and tally_left == last_left:
                            # DB changed! DB wins
                            resolved_left = db_left
                        elif tally_left != last_left and db_left == last_left:
                            # Tally changed! Tally wins
                            resolved_left = tally_left
                        elif tally_left != db_left:
                            # Conflict or first-time: Tally wins
                            resolved_left = tally_left
                            
                        self.sync_state[clean_en] = resolved_left
                        s["is_left"] = resolved_left
                        
                        db_differs = False
                        if not db_rec:
                            db_differs = True
                        else:
                            db_differs = self._records_differ(s, db_rec) or (db_left != resolved_left)
                            
                        if db_differs:
                            to_upsert_to_db.append(s)
                            if db_rec:
                                db_map[clean_en]["is_left"] = resolved_left
                    
                    # Check for students marked as Left 2026 in Tally but active in DB (who are not in students_list)
                    processed_enrollments = {str(s.get("enrollment_no")).strip() for s in students_list if s.get("enrollment_no")}
                    for en_key, db_rec in db_map.items():
                        if en_key in processed_enrollments:
                            continue
                        clean_en_lower = en_key.lower()
                        student_name = db_rec.get("student_name") or ""
                        expected_ledger_name = f"{student_name.strip()} -{db_rec['enrollment_no']}".lower() if student_name else en_key.lower()
                        
                        parent_group = tally_ledger_parents.get(clean_en_lower) or tally_ledger_parents.get(expected_ledger_name)
                        tally_left = bool(parent_group and (parent_group.startswith("Left") or parent_group.startswith("Passout")))
                        db_left = db_rec.get("is_left") in (True, "true", "True", "yes", "Yes", 1, "1")
                        
                        last_left = self.sync_state.get(en_key, False)
                        resolved_left = db_left
                        if db_left != last_left and tally_left == last_left:
                            resolved_left = db_left
                        elif tally_left != last_left and db_left == last_left:
                            resolved_left = tally_left
                        elif tally_left != db_left:
                            resolved_left = tally_left
                            
                        self.sync_state[en_key] = resolved_left
                        
                        if db_left != resolved_left:
                            logger.info(f"Student {en_key} status reconciliation: Tally left={tally_left}, DB left={db_left}, updating DB to {resolved_left}")
                            updated_rec = dict(db_rec)
                            updated_rec["is_left"] = resolved_left
                            to_upsert_to_db.append(updated_rec)
                            db_map[en_key]["is_left"] = resolved_left

                    if to_upsert_to_db:
                        logger.info(f"Syncing {len(to_upsert_to_db)} new/modified records into database...")
                        if settings.USE_SUPABASE:
                            processed, failed = self.supabase_client.upsert_students_batch(to_upsert_to_db, job_id)
                        elif settings.USE_ORACLE:
                            processed, failed = self.oracle_client.upsert_students_batch(to_upsert_to_db)
                    else:
                        logger.info("No new or modified records found in Tally to sync to database.")
                else:
                    logger.info("Tally to Database student sync route is disabled.")


                
                # B. DB -> Tally Sync (Reconcile Oracle/Supabase to Tally)
                reconciled_count = 0
                if not settings.DISABLE_DB_TO_TALLY:
                    if settings.USE_ORACLE:
                        logger.info("Checking Oracle DB for students with TALLY_SYNC = NULL or U (pending sync)...")
                        updated_students = self.oracle_client.get_recently_updated_students()
                        
                        if updated_students:
                            logger.info(f"Found {len(updated_students)} modified/unsynced student records in Oracle DB.")
                            
                            # Pre-verify and pre-create course groups and semester subgroups in Tally for pending students only
                            logger.info("Verifying and automatically pre-creating course groups and semester subgroups in Tally for pending sync students...")
                            from .tally_client import clean_group_name
                            unique_classes = set()
                            for student in updated_students:
                                cls = student.get("student_class")
                                if cls:
                                    cleaned = clean_group_name(cls)
                                    if cleaned:
                                        unique_classes.add(cleaned)
                            
                            # Sort and pre-create hierarchically (Student -> Main Course -> Semester Subgroup)
                            for cleaned_class in sorted(list(unique_classes)):
                                self.tally_client.create_group_in_tally(cleaned_class)
                            
                            # Fetch all ledger parent mappings and primary name maps from Tally once to avoid individual API queries
                            try:
                                tally_ledger_parents = self.tally_client.fetch_all_ledgers_with_parent()
                            except Exception as e:
                                logger.warning(f"Could not fetch ledger parent mappings: {e}")
                                tally_ledger_parents = {}
                                
                            try:
                                tally_ledger_primary_names = self.tally_client.fetch_all_ledgers_primary_names()
                            except Exception as e:
                                logger.warning(f"Could not fetch ledger primary name mappings: {e}")
                                tally_ledger_primary_names = {}
                                
                            max_updated_on = None
                            for db_rec in updated_students:
                                company_id = db_rec.get("company_id")
                                if not SyncState.get_enabled(company_id):
                                    continue
                                    
                                en_key = db_rec["enrollment_no"]
                                clean_en_lower = en_key.lower()
                                student_name = db_rec.get("student_name") or ""
                                expected_ledger_name = f"{student_name.strip()} -{db_rec['enrollment_no']}".lower() if student_name else clean_en_lower
                                
                                # Query Tally cached ledger parent map
                                parent_group = tally_ledger_parents.get(clean_en_lower) or tally_ledger_parents.get(expected_ledger_name)
                                    
                                in_tally = parent_group is not None
                                tally_left = bool(parent_group and (parent_group.startswith("Left") or parent_group.startswith("Passout")))
                                resolved_left = db_rec.get("is_left", False)
                                
                                mismatched_parent = False
                                if in_tally:
                                    if resolved_left and not tally_left:
                                        mismatched_parent = True
                                    elif not resolved_left and tally_left:
                                        mismatched_parent = True
                                
                                should_sync = False
                                action_desc = ""
                                
                                sync_new = SyncState.get_sync_new(company_id)
                                sync_modified = SyncState.get_sync_modified(company_id)
                                force_reconcile = SyncState.get_force_reconcile(company_id)
                                
                                if not in_tally:
                                    # Route 1: New student — create ledger in Tally
                                    if sync_new:
                                        should_sync = True
                                        action_desc = "CREATE_IN_TALLY"
                                else:
                                    # Route 2 & 3: Update existing ledger
                                    if sync_modified:
                                        should_sync = True
                                        action_desc = "UPDATE_IN_TALLY"
                                    elif force_reconcile:
                                        should_sync = True
                                        action_desc = "FORCE_RECONCILE"
                                    elif mismatched_parent:
                                        should_sync = True
                                        action_desc = "UPDATE_PARENT_IN_TALLY"
                                        
                                if should_sync:
                                    logger.info(f"Syncing student {en_key} to Tally ({action_desc})...")
                                    db_rec_copy = dict(db_rec)
                                    db_rec_copy.pop("updated_on", None)
                                    tally_name = tally_ledger_primary_names.get(clean_en_lower) or tally_ledger_primary_names.get(expected_ledger_name)
                                    success = self.tally_client.sync_student_to_tally(
                                        en_key, 
                                        db_rec_copy, 
                                        is_new=(not in_tally),
                                        tally_ledger_name=tally_name
                                    )
                                    if success:
                                        reconciled_count += 1
                                        # Mark TALLY_SYNC = 'S' — purely driven by our new column
                                        self.oracle_client.update_tally_sync_status(en_key, 'S')
                                    else:
                                        logger.error(f"Failed to sync student {en_key} to Tally.")
                                        # Leave TALLY_SYNC as 'U' — will be retried next cycle
                            
                            if reconciled_count > 0:
                                self.save_sync_state()
                                logger.info(f"Successfully synced {reconciled_count} students from Oracle DB to Tally.")

                        else:
                            logger.info("No modified or unsynced student records found in Oracle DB.")

                    elif settings.USE_SUPABASE:
                        # Fallback for Supabase (if ever reactivated)
                        for en_key, db_rec in db_map.items():
                            clean_en_lower = en_key.lower()
                            student_name = db_rec.get("student_name") or ""
                            expected_ledger_name = f"{student_name.strip()} -{db_rec['enrollment_no']}".lower() if student_name else en_key.lower()
                            
                            parent_group = tally_ledger_parents.get(clean_en_lower) or tally_ledger_parents.get(expected_ledger_name)
                            in_tally = parent_group is not None
                            
                            tally_left = bool(parent_group and (parent_group.startswith("Left") or parent_group.startswith("Passout")))
                            resolved_left = self.sync_state.get(en_key, False)
                            
                            mismatched_parent = False
                            if in_tally:
                                if resolved_left and not tally_left:
                                    mismatched_parent = True
                                elif not resolved_left and tally_left:
                                    mismatched_parent = True
                                    
                            if not in_tally or mismatched_parent:
                                action_desc = "RECONCILE_TO_TALLY" if not in_tally else "UPDATE_PARENT_IN_TALLY"
                                logger.info(f"Reconciling student {en_key} ({action_desc})...")
                                db_rec_copy = dict(db_rec)
                                db_rec_copy["is_left"] = resolved_left
                                success = self.tally_client.sync_student_to_tally(db_rec["enrollment_no"], db_rec_copy, is_new=(not in_tally))
                                if success:
                                    reconciled_count += 1
                                    self.supabase_client.log_student_sync(job_id, db_rec["enrollment_no"], "SUCCESS", action=action_desc)
                                else:
                                    self.supabase_client.log_student_sync(job_id, db_rec["enrollment_no"], "FAILED", action=action_desc, error_message="Tally write failed")
                        
                        self.save_sync_state()
                        
                        if reconciled_count > 0:
                            logger.info(f"Reconciled {reconciled_count} students from Supabase to Tally.")
                else:
                    logger.info("Database to Tally student sync route is disabled.")

                
                # C. Sync Transactions (Automated via API + Manual Fallback)
                tx_processed = 0
                tx_failed = 0
                tx_total = 0
                if not settings.DISABLE_TRANSACTION_SYNC:
                    try:
                        import os
                        
                        # 1. Fetch from Tally API (Automated Realtime Sync)
                        logger.info("Fetching recent transactions from Tally API...")
                        api_tx_xml = self.tally_client.fetch_transactions()
                        
                        if api_tx_xml:
                            logger.info("Parsing transactions XML from API...")
                            transactions_list = parse_transactions_xml(api_tx_xml)
                            tx_total += len(transactions_list)
                            
                            if transactions_list:
                                logger.info("Fetching current transaction records from Supabase for delta check...")
                                res_tx = self.supabase_client.client.table("fee_transactions").select("guid, amount, raw_payload").execute()
                                db_tx_map = {row["guid"]: row for row in res_tx.data or []}
                                
                                import json
                                to_upsert_tx = []
                                for tx in transactions_list:
                                    guid = tx.get("guid")
                                    if not guid:
                                        continue
                                    if guid not in db_tx_map:
                                        to_upsert_tx.append(tx)
                                    else:
                                        db_tx = db_tx_map[guid]
                                        if self._check_numeric_diff(tx.get("amount"), db_tx.get("amount")):
                                            to_upsert_tx.append(tx)
                                        else:
                                            tx_payload = json.dumps(tx.get("raw_payload", {}), sort_keys=True)
                                            db_payload = json.dumps(db_tx.get("raw_payload", {}), sort_keys=True)
                                            if tx_payload != db_payload:
                                                to_upsert_tx.append(tx)

                                if to_upsert_tx:
                                    logger.info(f"Syncing {len(to_upsert_tx)} new/modified transaction records into Supabase...")
                                    api_p, api_f = self.supabase_client.upsert_transactions_batch(to_upsert_tx, job_id)
                                    tx_processed += api_p
                                    tx_failed += api_f
                                else:
                                    logger.info("No new or modified fee transactions found in Tally API response.")

                                # --- Automated Deletion Sync ---
                                tally_guids = {tx.get("guid") for tx in transactions_list if tx.get("guid")}
                                parsed_dates = []
                                for tx in transactions_list:
                                    d_str = tx.get("date")
                                    if d_str:
                                        try:
                                            from datetime import datetime
                                            parsed_dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
                                        except Exception:
                                            pass
                                
                                if parsed_dates:
                                    min_date = min(parsed_dates)
                                    max_date = max(parsed_dates)
                                    logger.info(f"Analyzing deleted transactions within current Tally date range boundary: {min_date} to {max_date}...")
                                    
                                    # Fetch transactions in Supabase that are within this date range
                                    try:
                                        res_range = self.supabase_client.client.table("fee_transactions").select("guid, date").gte("date", min_date.isoformat()).lte("date", max_date.isoformat()).execute()
                                        db_range_tx = res_range.data or []
                                        
                                        guids_to_delete = []
                                        for db_tx in db_range_tx:
                                            db_guid = db_tx.get("guid")
                                            if db_guid and db_guid not in tally_guids:
                                                guids_to_delete.append(db_guid)
                                                
                                        if guids_to_delete:
                                            logger.info(f"Detected {len(guids_to_delete)} transactions deleted in Tally. Synchronizing deletions to Supabase...")
                                            for g_del in guids_to_delete:
                                                try:
                                                    self.supabase_client.client.table("fee_transactions").delete().eq("guid", g_del).execute()
                                                    logger.info(f"Automatically deleted transaction {g_del} in Supabase (Sync complete)")
                                                except Exception as del_err:
                                                    logger.error(f"Failed to automatically delete transaction {g_del}: {str(del_err)}")
                                    except Exception as range_err:
                                        logger.error(f"Failed during automated transaction deletion query: {str(range_err)}")
                            else:
                                logger.info("No valid fee transactions found in Tally API response.")
                                
                        # 2. Process manual Transactions.xml drop if exists (Historical Fallback)
                        if os.path.exists('Transactions.xml'):
                            logger.info("Manual Transactions.xml found! Reading for fee transactions sync...")
                            try:
                                with open('Transactions.xml', 'r', encoding='utf-16') as f:
                                    tx_xml_data = f.read()
                            except UnicodeDecodeError:
                                with open('Transactions.xml', 'r', encoding='utf-8-sig') as f:
                                    tx_xml_data = f.read()
                            
                            logger.info("Parsing manual transactions XML...")
                            manual_tx_list = parse_transactions_xml(tx_xml_data)
                            tx_total += len(manual_tx_list)
                            
                            if manual_tx_list:
                                logger.info(f"Syncing {len(manual_tx_list)} manual transaction records into Supabase...")
                                man_p, man_f = self.supabase_client.upsert_transactions_batch(manual_tx_list, job_id)
                                tx_processed += man_p
                                tx_failed += man_f
                                
                            os.rename('Transactions.xml', 'Transactions.xml.processed')
                            
                    except Exception as tx_err:
                        logger.error(f"Failed during transaction sync process: {str(tx_err)}")
                        logger.error(traceback.format_exc())
                else:
                    logger.info("Transaction sync route is disabled.")
 
                
                # 6. Complete job record
                if settings.USE_SUPABASE:
                    self.supabase_client.update_sync_job(
                        job_id=job_id,
                        status="COMPLETED",
                        total=total_count + tx_total,
                        processed=processed + reconciled_count + tx_processed,
                        failed=failed + tx_failed
                    )
                from datetime import datetime
                SyncState.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Sync cycle finished successfully. Processed Students: {processed}, Reconciled: {reconciled_count}, Transactions: {tx_processed}, Total Failed: {failed + tx_failed}")
                return failed == 0

                
            except Exception as e:
                err_msg = f"Critical error during sync cycle: {str(e)}"
                logger.error(err_msg)
                logger.error(traceback.format_exc())
                
                if settings.USE_SUPABASE and job_id and self.supabase_client:
                    try:
                        self.supabase_client.update_sync_job(
                            job_id=job_id,
                            status="FAILED",
                            total=0,
                            processed=0,
                            failed=0
                        )
                    except Exception as db_err:
                        logger.error(f"Failed to record final failure status for job {job_id}: {str(db_err)}")
                return False
        finally:
            import time
            time.sleep(10) # Safely ignore all trailing realtime events triggered by this sync cycle
            self.is_syncing = False

    async def process_realtime_event(self, payload: dict):
        """
        Processes a Supabase Realtime database change event.
        """
        try:
            logger.info(f"REALTIME EVENT RECEIVED: {payload}")
            
            # realtime-py nests the payload inside 'data'
            data = payload.get("data", payload)
            
            event_type = data.get("eventType") or data.get("type")
            if hasattr(event_type, 'value'):
                event_type = event_type.value
                
            table_name = data.get("table")
            
            if event_type not in ("INSERT", "UPDATE"):
                logger.debug(f"Ignoring non-UPSERT event: {event_type}")
                return

            if self.is_syncing:
                logger.debug(f"Ignoring event {event_type} as scheduled sync cycle is currently running.")
                return

            if table_name == "fee_transactions":
                if settings.DISABLE_TRANSACTION_SYNC:
                    logger.info("Realtime transaction sync is disabled. Skipping event.")
                    return
                await self._process_transaction_event(data, event_type)
                return
            elif table_name == "fee_allocations":
                if settings.DISABLE_TRANSACTION_SYNC:
                    logger.info("Realtime allocation sync is disabled. Skipping event.")
                    return
                await self._process_allocation_event(data, event_type)
                return
            elif table_name != "students":
                return

            if settings.DISABLE_DB_TO_TALLY:
                logger.info("Realtime DB to Tally student sync is disabled. Skipping event.")
                return

            student_data = data.get("record") or data.get("new", {})

            enrollment_no = student_data.get("enrollment_no")
            if not enrollment_no:
                logger.warning(f"Realtime event payload has no enrollment_no: {payload}")
                return

            old_data = data.get("old_record") or data.get("old", {})

            # If old_data exists and has more keys than just enrollment_no, compare relevant fields
            if len(old_data) > 1:
                relevant_fields = [
                    "student_name", "student_class", "opening_balance", "closing_balance",
                    "father_name", "mother_name", "religion", "gender", "roll_no",
                    "course", "session", "year", "mobile", "caste", "category",
                    "registration_no", "dob", "admission_category", "rank",
                    "annual_income", "permanent_pin", "correspondence_pin",
                    "status", "substatus", "is_left"
                ]
                changed = False
                for field in relevant_fields:
                    if field in student_data and student_data[field] != old_data.get(field):
                        changed = True
                        break
                if not changed:
                    logger.debug(f"No relevant fields changed for student {enrollment_no}. Skipping sync.")
                    return

            action = "Create" if event_type == "INSERT" else "Alter"
            logger.info(f"Realtime sync triggered for student {enrollment_no} ({action}) due to database changes.")

            # Send alteration to Tally
            is_new = (event_type == "INSERT")
            tally_name = None
            if not is_new:
                try:
                    primary_names = self.tally_client.fetch_all_ledgers_primary_names()
                    clean_en_lower = str(enrollment_no).strip().lower()
                    student_name = student_data.get("student_name") or ""
                    expected_ledger_name = f"{student_name.strip()} -{enrollment_no}".lower() if student_name else clean_en_lower
                    tally_name = primary_names.get(clean_en_lower) or primary_names.get(expected_ledger_name)
                except Exception as e:
                    logger.warning(f"Could not fetch primary name mapping in realtime handler: {e}")
             
            success = self.tally_client.sync_student_to_tally(
                enrollment_no, 
                student_data, 
                is_new=is_new,
                tally_ledger_name=tally_name
            )

            if success:
                # Update in-memory state and save it
                is_left_db = student_data.get("is_left")
                is_left_db_bool = is_left_db in (True, "true", "True", "yes", "Yes", 1, "1")
                self.sync_state[enrollment_no] = is_left_db_bool
                self.save_sync_state()

            # Lazy initialize supabase sync client to record the logs
            if self._init_supabase():
                status = "SUCCESS" if success else "FAILED"
                err_msg = None if success else "Tally alteration failed. Check agent log."
                try:
                    self.supabase_client.log_student_sync(
                        job_id=None,
                        enrollment_no=enrollment_no,
                        status=status,
                        action=f"REALTIME_{action.upper()}",
                        error_message=err_msg
                    )
                except Exception as log_err:
                    logger.error(f"Failed to log realtime sync trace in database for {enrollment_no}: {log_err}")

        except Exception as e:
            logger.error(f"Error processing realtime change event: {str(e)}")
            logger.error(traceback.format_exc())

    async def _sync_transaction_by_guid(self, guid: str, action: str):
        if not self._init_supabase():
            logger.error("Database connection missing. Cannot fetch transaction details.")
            return
            
        # Fetch full transaction with allocations and student data
        full_tx = self.supabase_client.get_transaction_with_allocations(guid)
        if not full_tx:
            logger.error(f"Could not fetch full transaction details for {guid}")
            return
            
        # Validate that amount matches allocations sum
        amount = float(full_tx.get("amount", 0.0))
        allocations = full_tx.get("fee_allocations", [])
        allocations_sum = sum(float(a.get("amount", 0.0)) for a in allocations)
        
        # Tally is extremely strict: total credits must match total debits and bill allocations sum must match ledger entry amount
        if abs(amount - allocations_sum) > 0.01:
            logger.warning(f"Transaction amount ({amount:.2f}) does not match allocations sum ({allocations_sum:.2f}) for transaction {guid}. Skipping sync to Tally until they balance in the database.")
            return
            
        logger.info(f"Pushing transaction {guid} (amount: {amount:.2f}) to Tally...")
        # Send alteration to Tally
        success = self.tally_client.sync_transaction_to_tally(full_tx)
        
        status = "SUCCESS" if success else "FAILED"
        err_msg = None if success else "Tally alteration failed. Check agent log."
        try:
            self.supabase_client.log_transaction_sync(
                job_id=None,
                transaction_guid=guid,
                status=status,
                action=f"REALTIME_{action.upper()}",
                error_message=err_msg
            )
        except Exception as log_err:
            logger.error(f"Failed to log transaction sync trace for {guid}: {log_err}")

    async def _process_transaction_event(self, data: dict, event_type: str):
        transaction_data = data.get("record") or data.get("new", {})
        guid = transaction_data.get("guid")
        if not guid:
            logger.warning(f"Realtime event payload has no guid: {data}")
            return
            
        old_data = data.get("old_record") or data.get("old", {})
        if len(old_data) > 1:
            if transaction_data.get("amount") == old_data.get("amount"):
                logger.debug(f"Transaction amount didn't change for {guid}. Skipping sync to Tally.")
                return
                
        action = "Create" if event_type == "INSERT" else "Alter"
        logger.info(f"Realtime sync triggered for transaction {guid} ({action}) due to database changes. Waiting 2.0s for allocations...")
        
        # Wait a brief moment to let related allocations commit
        await asyncio.sleep(2.0)
        await self._sync_transaction_by_guid(guid, action)

    async def _process_allocation_event(self, data: dict, event_type: str):
        allocation_data = data.get("record") or data.get("new", {})
        tx_guid = allocation_data.get("transaction_guid")
        if not tx_guid:
            logger.warning(f"Realtime allocation event payload has no transaction_guid: {data}")
            return
            
        action = "Alter"
        logger.info(f"Realtime sync triggered for parent transaction {tx_guid} ({action}) due to allocation changes. Waiting 2.0s for transaction...")
        
        # Wait a brief moment to let related transaction updates commit
        await asyncio.sleep(2.0)
        await self._sync_transaction_by_guid(tx_guid, action)

    async def run_realtime_listener(self):
        """
        Persistent listener loop that subscribes to Supabase Realtime changes on 'students' table.
        Runs indefinitely with backoff reconnection logic.
        """
        backoff = 1
        while True:
            try:
                logger.info("Initializing Realtime Supabase async client...")
                supabase = await acreate_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
                channel = supabase.channel("students_realtime")
                
                def on_change(payload):
                    asyncio.create_task(self.process_realtime_event(payload))

                def on_subscribe(status, err=None):
                    if err:
                        logger.error(f"Supabase Realtime subscription status: {status}, error: {err}")
                    else:
                        logger.info(f"Supabase Realtime subscription status: {status}")

                await channel.on_postgres_changes(
                    event="*",
                    schema="public",
                    table="students",
                    callback=on_change
                ).on_postgres_changes(
                    event="*",
                    schema="public",
                    table="fee_transactions",
                    callback=on_change
                ).subscribe(on_subscribe)
                
                backoff = 1
                
                while True:
                    await asyncio.sleep(3600)
                    
            except asyncio.CancelledError:
                logger.info("Realtime listener loop canceled.")
                break
            except Exception as e:
                logger.error(f"Supabase Realtime connection failed: {str(e)}. Retrying in {backoff} seconds...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

