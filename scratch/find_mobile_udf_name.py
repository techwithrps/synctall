import re

def search_mobile_udf():
    with open("Master.xml", "rb") as f:
        content = f.read().decode("utf-16")
        
    print("Searching for mobile numbers in Master.xml UDFs...")
    # Look for tags around mobile numbers we found in student_details_raw.xml
    # For example: 8542956522, 7860355000, 9161403498
    mobiles = ["8542956522", "7860355000", "9161403498"]
    for m in mobiles:
        # Search for occurrences of the mobile number inside XML tags
        pattern = rf'<([^>]+)>([^<]*{m}[^<]*)</\1>'
        matches = re.findall(pattern, content)
        if matches:
            print(f"Found matches for {m}:", matches)
        else:
            print(f"No tag matches for {m}")

search_mobile_udf()
