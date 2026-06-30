import re

def search_address_udf():
    with open("Master.xml", "rb") as f:
        content = f.read().decode("utf-16")
        
    print("Searching for address-related tags in Master.xml...")
    
    # We saw in the branch output or student_details_raw.xml some address text.
    # Let's search for tags that contain typical address text like "Uttar Pradesh" or "Himachal Pradesh"
    # and see if there are custom UDF list tags.
    # Standard address is usually in <ADDRESS> under <ADDRESS.LIST>.
    # But let's find if there are UDF tags with ADDRESS in the name.
    udf_tags = set(re.findall(r'<(UDF:[^>]*ADDRESS[^>]*)>', content, re.IGNORECASE))
    print("Found UDF tags containing 'ADDRESS':", udf_tags)

search_address_udf()
