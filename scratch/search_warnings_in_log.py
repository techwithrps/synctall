log_file = "C:\\Users\\F-tech\\.gemini\\antigravity-ide\\brain\\29163ea9-eb6e-435c-b5df-6a27d59a307c\\.system_generated\\tasks\\task-879.log"

try:
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            if any(w in line.lower() for w in ["pausing", "offline", "warning", "exception"]):
                print(f"Line {idx+1}: {line.strip()}")
except Exception as e:
    print("Error:", e)
