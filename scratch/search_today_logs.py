import os

log_dir = "c:\\Users\\F-tech\\Desktop\\codify\\synctal\\logs"
log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if "log" in f]

for log_file in log_files:
    if not os.path.isfile(log_file):
        continue
    try:
        printed = 0
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "2026-06-24" in line:
                    # Let's print lines that mention student or sync or update
                    if any(w in line.lower() for w in ["student", "sync", "oracle", "tally", "updating", "marked"]):
                        # Print if it's not a repeating "route is disabled" log
                        if "route is disabled" not in line and "finished successfully" not in line:
                            print(f"{os.path.basename(log_file)}: {line.strip()}")
                            printed += 1
                            if printed > 150:
                                print("... truncated ...")
                                break
    except Exception as e:
        print(f"Error reading {log_file}: {e}")
