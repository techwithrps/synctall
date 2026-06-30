import os
import json

app_data_dir = r"C:\Users\F-tech\.gemini\antigravity-ide"
conv_id = "29163ea9-eb6e-435c-b5df-6a27d59a307c"
transcript_path = os.path.join(app_data_dir, "brain", conv_id, ".system_generated", "logs", "transcript.jsonl")

if os.path.exists(transcript_path):
    print("Found transcript file. Searching for mentions of status updates or counts...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                content = str(data.get("content", ""))
                # Search for 54 or 2 or status update commands
                if "54" in content or "UPDATE" in content or "TALLY_SYNC" in content:
                    # Print step details
                    print(f"Step {data.get('step_index')}: {content[:300]}")
            except Exception as e:
                pass
else:
    print("Transcript not found at path:", transcript_path)
