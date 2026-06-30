import re

def search_add_udfs():
    with open("Master.xml", "rb") as f:
        content = f.read().decode("utf-16")
        
    print("Searching for UDFs containing 'ADD' or 'CORS' or 'CORR' in Master.xml...")
    udf_tags = set(re.findall(r'<(UDF:[^>]*ADD[^>]*|UDF:[^>]*CORS[^>]*|UDF:[^>]*CORR[^>]*)>', content, re.IGNORECASE))
    print("Found UDF tags:", sorted(list(udf_tags)))

search_add_udfs()
