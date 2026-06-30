import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client
from .config import settings
from .logger import setup_logger

logger = setup_logger("supabase_client", settings.LOG_LEVEL)

class SupabaseSyncClient:
    def __init__(self):
        """
        Initializes Supabase API client. Uses service-role keys from .env context.
        """
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_ROLE_KEY
        logger.info(f"Initializing Supabase client targeting project URL: {url}")
        self.client: Client = create_client(url, key)
        
    def start_sync_job(self) -> str:
        """
        Creates a new synchronization job inside 'sync_jobs' table.
        Returns: The UUID string of the newly created sync job.
        """
        try:
            job_data = {
                "status": "PROCESSING",
                "total": 0,
                "processed": 0,
                "failed": 0
            }
            res = self.client.table("sync_jobs").insert(job_data).execute()
            if res.data and len(res.data) > 0:
                job_id = res.data[0]["id"]
                logger.info(f"Started Sync Job inside Supabase: {job_id}")
                return job_id
            raise ValueError("No rows returned from Supabase insert confirmation.")
        except Exception as e:
            logger.error(f"Failed to record sync start event in database: {str(e)}")
            raise

    def get_pending_sync_job(self) -> Optional[str]:
        """
        Polls the sync_jobs table to check if there is an immediately pending manual sync request.
        Returns: The UUID of the oldest pending sync job, or None.
        """
        try:
            res = self.client.table("sync_jobs").select("id").eq("status", "PENDING").order("created_at", desc=False).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["id"]
            return None
        except Exception as e:
            logger.error(f"Failed to query database for PENDING sync requests: {str(e)}")
            return None

    def claim_sync_job(self, job_id: str) -> None:
        """
        Claims a pending sync job by transitioning its status from PENDING to PROCESSING.
        """
        try:
            self.client.table("sync_jobs").update({"status": "PROCESSING"}).eq("id", job_id).execute()
            logger.info(f"Successfully claimed sync job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to transition claimed job state to PROCESSING: {str(e)}")
            raise

    def update_sync_job(self, job_id: str, status: str, total: int, processed: int, failed: int) -> None:
        """
        Updates the final execution outcome metadata of a sync job.
        """
        try:
            update_data = {
                "status": status,
                "total": total,
                "processed": processed,
                "failed": failed,
                "completed_at": datetime.utcnow().isoformat()
            }
            self.client.table("sync_jobs").update(update_data).eq("id", job_id).execute()
            logger.info(f"Updated sync job {job_id} to status: {status} (Total: {total}, Processed: {processed}, Failed: {failed})")
        except Exception as e:
            logger.error(f"Failed to log sync completion parameters in database for {job_id}: {str(e)}")

    def log_student_sync(self, job_id: str, enrollment_no: str, status: str, action: str = "UPSERT", error_message: str = None) -> None:
        """
        Logs individual student transaction trace for audit logging.
        """
        try:
            log_data = {
                "job_id": job_id,
                "enrollment_no": enrollment_no,
                "status": status,
                "action": action
            }
            if error_message:
                log_data["error_message"] = error_message[:1000]
            self.client.table("student_sync_logs").insert(log_data).execute()
        except Exception as e:
            logger.error(f"Failed to log student sync trace in database for {enrollment_no}: {str(e)}")

    def upsert_students_batch(self, students: List[Dict[str, Any]], job_id: str, batch_size: int = 100) -> Tuple[int, int]:
        """
        Upserts a list of parsed student records into Supabase in structured batches.
        Falls back to individual line-by-line upserts if a batch fails, to isolate faulty rows.
        """
        processed_count = 0
        failed_count = 0
        
        sync_time = datetime.utcnow().isoformat()
        for s in students:
            s["last_synced_at"] = sync_time
            
        # Segment into batch chunks
        for i in range(0, len(students), batch_size):
            batch = students[i:i + batch_size]
            logger.info(f"Upserting student batch {i//batch_size + 1} of {(len(students)-1)//batch_size + 1} (Batch size: {len(batch)})")
            
            try:
                # Perform batch upsert targeting primary key enrollment_no
                self.client.table("students").upsert(batch, on_conflict="enrollment_no").execute()
                processed_count += len(batch)
                
                # Log success traces
                for s_item in batch:
                    self.log_student_sync(job_id, s_item["enrollment_no"], "SUCCESS")
                    
            except Exception as e:
                # Batch failed, rollback to individual upserts to allow partial success
                logger.warning(f"Batch upsert failed: {str(e)}. Retrying records individually within this batch...")
                
                for s_item in batch:
                    try:
                        self.client.table("students").upsert([s_item], on_conflict="enrollment_no").execute()
                        processed_count += 1
                        self.log_student_sync(job_id, s_item["enrollment_no"], "SUCCESS")
                    except Exception as err:
                        failed_count += 1
                        err_msg = str(err)
                        logger.error(f"Record upsert failed for {s_item.get('enrollment_no')}: {err_msg}")
                        self.log_student_sync(
                            job_id=job_id,
                            enrollment_no=s_item.get("enrollment_no", "UNKNOWN"),
                            status="FAILED",
                            error_message=err_msg
                        )
                        
        return processed_count, failed_count

    def log_transaction_sync(self, job_id: str, transaction_guid: str, status: str, action: str = "UPSERT", error_message: str = None) -> None:
        """
        Logs individual fee transaction trace for audit logging.
        """
        try:
            log_data = {
                "job_id": job_id,
                "transaction_guid": transaction_guid,
                "status": status,
                "action": action
            }
            if error_message:
                log_data["error_message"] = error_message[:1000]
            self.client.table("transaction_sync_logs").insert(log_data).execute()
        except Exception as e:
            logger.error(f"Failed to log transaction sync trace in database for {transaction_guid}: {str(e)}")

    def upsert_transactions_batch(self, transactions: List[Dict[str, Any]], job_id: str, batch_size: int = 100) -> Tuple[int, int]:
        """
        Upserts a list of parsed transaction records and their allocations into Supabase in batches.
        """
        processed_count = 0
        failed_count = 0
        
        sync_time = datetime.utcnow().isoformat()
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            logger.info(f"Upserting transaction batch {i//batch_size + 1} of {(len(transactions)-1)//batch_size + 1} (Batch size: {len(batch)})")
            
            for tx in batch:
                tx_guid = tx["guid"]
                try:
                    # Prepare transaction record
                    tx_record = {
                        "guid": tx_guid,
                        "date": tx["date"],
                        "voucher_number": tx["voucher_number"],
                        "voucher_type": tx["voucher_type"],
                        "party_ledger_name": tx["party_ledger_name"],
                        "particulars": tx.get("particulars"),
                        "enrollment_no": tx["enrollment_no"],
                        "amount": tx["amount"],
                        "raw_payload": tx["raw_payload"],
                        "last_synced_at": sync_time
                    }
                    
                    # Upsert transaction
                    self.client.table("fee_transactions").upsert(tx_record, on_conflict="guid").execute()
                    
                    # Delete existing allocations for this transaction to replace them
                    self.client.table("fee_allocations").delete().eq("transaction_guid", tx_guid).execute()
                    
                    # Insert allocations
                    if tx.get("allocations"):
                        alloc_records = []
                        for alloc in tx["allocations"]:
                            alloc_records.append({
                                "transaction_guid": tx_guid,
                                "bill_name": alloc["bill_name"],
                                "bill_type": alloc["bill_type"],
                                "amount": alloc["amount"],
                                "fee_head": alloc["fee_head"],
                                "semester": alloc["semester"],
                                "last_synced_at": sync_time
                            })
                        self.client.table("fee_allocations").insert(alloc_records).execute()
                        
                    processed_count += 1
                    self.log_transaction_sync(job_id, tx_guid, "SUCCESS")
                    
                except Exception as err:
                    failed_count += 1
                    err_msg = str(err)
                    logger.error(f"Transaction upsert failed for {tx_guid}: {err_msg}")
                    self.log_transaction_sync(
                        job_id=job_id,
                        transaction_guid=tx_guid,
                        status="FAILED",
                        error_message=err_msg
                    )
                    
        return processed_count, failed_count

    def get_transaction_with_allocations(self, transaction_guid: str) -> Optional[Dict[str, Any]]:
        """
        Fetches a transaction, its allocations, and the associated student info.
        """
        try:
            res = self.client.table("fee_transactions").select(
                "*, "
                "fee_allocations(*), "
                "students(*)"
            ).eq("guid", transaction_guid).execute()
            
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch transaction {transaction_guid} from Supabase: {str(e)}")
            return None
