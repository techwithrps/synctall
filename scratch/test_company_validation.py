import sys
from sync_agent.sync_service import SyncService

def run_test():
    print("Initializing SyncService...")
    service = SyncService()
    
    print("\nCalling validate_active_company()...")
    result = service.validate_active_company()
    print(f"\nValidation Result: {result}")
    
if __name__ == "__main__":
    run_test()
