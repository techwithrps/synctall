log_file = "C:\\Users\\F-tech\\.gemini\\antigravity-ide\\brain\\29163ea9-eb6e-435c-b5df-6a27d59a307c\\.system_generated\\tasks\\task-879.log"

try:
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    print(f"Total lines in log: {len(lines)}")
    print("--- LAST 50 LINES ---")
    for line in lines[-50:]:
        print(line.strip())
except Exception as e:
    print("Error:", e)
