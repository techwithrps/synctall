import time
import sys
import signal
import argparse
import asyncio
import threading
from sync_agent.config import settings
from sync_agent.logger import setup_logger
from sync_agent.sync_service import SyncService

logger = setup_logger("main", settings.LOG_LEVEL)

def start_realtime_thread(sync_service: SyncService):
    """
    Spawns a daemon thread to run the asynchronous Supabase realtime listener loop.
    """
    def run():
        logger.info("Starting background RealtimeListener async event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(sync_service.run_realtime_listener())
    t = threading.Thread(target=run, name="RealtimeListener", daemon=True)
    t.start()
    logger.info("RealtimeListener thread spawned successfully.")

def start_dashboard_thread():
    """
    Spawns a daemon thread to run the HTTP control dashboard web server.
    """
    from sync_agent.web_server import start_server
    def run():
        start_server(port=8080)
    t = threading.Thread(target=run, name="ControlDashboard", daemon=True)
    t.start()
    logger.info("Control dashboard thread spawned successfully.")

class GracefulKiller:
    kill_now = False
    def __init__(self):
        """
        Gracefully handles system interrupt and termination signals.
        """
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        logger.info(f"System interrupt signal received ({signum}). Gracefully exiting daemon loop...")
        self.kill_now = True

def main():
    parser = argparse.ArgumentParser(description="Tally ERP / Prime Student Database Synchronization Agent")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Executes a single immediate synchronization pass and terminates"
    )
    args = parser.parse_args()

    logger.info("==========================================================")
    logger.info("Starting Tally EDU college management integration platform")
    logger.info(f"Configured Sync Interval: {settings.SYNC_INTERVAL_SECONDS} seconds")
    logger.info(f"Tally URL Endpoint: {settings.TALLY_URL}")
    logger.info(f"Supabase Endpoint: {settings.SUPABASE_URL}")
    logger.info("==========================================================")

    sync_service = SyncService()

    # Isolated manual execution pass
    if args.once:
        logger.info("Executing isolated manual sync pass (--once option)...")
        success = sync_service.run_sync_cycle()
        sys.exit(0 if success else 1)

    killer = GracefulKiller()
    interval = settings.SYNC_INTERVAL_SECONDS
    last_scheduled_run = 0.0

    # Start the realtime listener in a background daemon thread if Supabase is enabled
    if settings.USE_SUPABASE:
        start_realtime_thread(sync_service)
    else:
        logger.info("Supabase is disabled. Realtime listener thread bypassed.")

    # Start the HTTP control dashboard server in a background daemon thread
    start_dashboard_thread()

    logger.info("Entering background synchronization loop...")
    while not killer.kill_now:
        try:
            current_time = time.time()
            
            # 1. Scheduled run check
            run_scheduled = (current_time - last_scheduled_run) >= interval
            
            # 2. Immediate remote trigger check (Pending jobs in DB)
            has_pending = False
            if settings.USE_SUPABASE and sync_service._init_supabase():
                pending_id = sync_service.supabase_client.get_pending_sync_job()
                if pending_id:
                    logger.info("Immediate remote trigger detected (PENDING job in database)!")
                    has_pending = True
            
            # 3. Trigger sync cycle if either condition is met
            if run_scheduled or has_pending:
                sync_service.run_sync_cycle()
                last_scheduled_run = time.time()
                
        except Exception as e:
            logger.critical(f"Unhandled sync loop failure: {str(e)}")
            
        # Poll sleep loop in 5 second checkpoints to allow responsive kills and pending checks
        slept = 0
        while slept < 5 and not killer.kill_now:
            time.sleep(1)
            slept += 1

    logger.info("Tally sync agent background service gracefully stopped.")

if __name__ == "__main__":
    main()
