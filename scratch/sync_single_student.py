from sync_agent.oracle_client import OracleSyncClient
from sync_agent.tally_client import TallyClient
import requests
import xml.etree.ElementTree as ET

oracle = OracleSyncClient()
tally = TallyClient()

enrl_no = "GF202453756"
students = oracle.get_all_students()
student = None
for s in students:
    if s.get("enrollment_no") == enrl_no:
        student = s
        break

if not student:
    print(f"Student {enrl_no} not found in Oracle!")
else:
    # Set parent class to Sundry Debtors if group creation fails or to keep it simple
    student_class = student.get("student_class")
    
    # We want to see what XML payload tally_client.sync_student_to_tally sends, so let's call it and inspect
    # Or write a small helper to generate it:
    # Let's inspect tally.create_group_in_tally(student_class)
    print("Creating parent group in Tally...")
    tally.create_group_in_tally(student_class)
    
    print("Syncing student to Tally...")
    # Temporarily monkeypatch/inject logging to stdout for requests
    import logging
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Let's intercept response by writing our own post function
    old_post = requests.post
    def new_post(url, *args, **kwargs):
        print("\n--- SENDING PAYLOAD ---")
        print(kwargs.get('data'))
        res = old_post(url, *args, **kwargs)
        print("\n--- RECEIVED RESPONSE ---")
        print(res.text)
        return res
    requests.post = new_post
    
    success = tally.sync_student_to_tally(enrl_no, student, is_new=True)
    print("\nSync Status:", "SUCCESS" if success else "FAILED")
