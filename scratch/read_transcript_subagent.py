import json

transcript_path = "C:\\Users\\F-tech\\.gemini\\antigravity-ide\\brain\\29163ea9-eb6e-435c-b5df-6a27d59a307c\\.system_generated\\logs\\transcript.jsonl"
transcript_full_path = "C:\\Users\\F-tech\\.gemini\\antigravity-ide\\brain\\29163ea9-eb6e-435c-b5df-6a27d59a307c\\.system_generated\\logs\\transcript_full.jsonl"

def search_file(path):
    print(f"Searching {os.path.basename(path)}...")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                # Parse as JSON if possible
                try:
                    obj = json.loads(line)
                    content = str(obj.get("content", ""))
                    tool_calls = str(obj.get("tool_calls", ""))
                    
                    # Search for student enrollment prefixes like UGO or PGO or specific keywords
                    # Or search for reports containing list of students
                    combined = content + " " + tool_calls
                    if "ugo" in combined.lower() or "pgo" in combined.lower() or "pending sync" in combined.lower():
                        # Print some context around the match
                        print(f"Step {obj.get('step_index')}: {combined[:500]}...")
                        # If the content contains an array of students or DOM structure, print it in full
                        if "ugo" in combined.lower() or "pgo" in combined.lower():
                            print("FULL CONTENT:")
                            print(content[:2000])
                            print("="*40)
                except Exception as je:
                    pass
    except Exception as e:
        print("Error:", e)

import os
search_file(transcript_path)
print("\n--- SEARCHING FULL TRANSCRIPT ---")
search_file(transcript_full_path)
