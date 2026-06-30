import os

log_dir = "c:\\Users\\F-tech\\Desktop\\codify\\synctal\\logs"
log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if "log" in f]

for log_file in log_files:
    if not os.path.isfile(log_file):
        continue
    print(f"=== SEARCHING {os.path.basename(log_file)} FOR UGO/PGO ===")
    try:
        count = 0
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "ugo" in line.lower() or "pgo" in line.lower():
                    print(line.strip())
                    count += 1
                    if count > 50:
                        print("... truncated ...")
                        break
    except Exception as e:
        print(f"Error: {e}")
