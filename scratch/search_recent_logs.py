import os

log_dir = "c:\\Users\\F-tech\\Desktop\\codify\\synctal\\logs"
log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if "log" in f]

for log_file in log_files:
    if not os.path.isfile(log_file):
        continue
    print(f"=== SEARCHING {os.path.basename(log_file)} ===")
    try:
        count = 0
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "2026-06-24" in line or "2026-06-23" in line:
                    # Print lines that have "student" or "sync" or enrollment patterns
                    if any(w in line.lower() for w in ["student", "sync", "enrl", "tally_sync"]):
                        print(line.strip())
                        count += 1
                        if count > 100:
                            print("... truncated after 100 lines ...")
                            break
    except Exception as e:
        print(f"Error reading {log_file}: {e}")
