log_file = "C:\\Users\\F-tech\\.gemini\\antigravity-ide\\brain\\29163ea9-eb6e-435c-b5df-6a27d59a307c\\.system_generated\\tasks\\task-879.log"

try:
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f):
            # Print if line contains traceback, exception, or critical error
            if any(w in line.lower() for w in ["traceback", "exception", "critical", "error"]):
                # But filter out the common Tally group creation error we already know
                if "could not set" not in line.lower() and "already a child" not in line.lower() and "tally_client.py:731" not in line.lower():
                    print(f"Line {idx+1}: {line.strip()}")
except Exception as e:
    print("Error:", e)
