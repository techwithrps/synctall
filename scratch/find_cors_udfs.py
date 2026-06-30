import re

def search_cors_udfs():
    with open("Master.xml", "rb") as f:
        content = f.read().decode("utf-16")
        
    print("Searching for 'CORS' UDFs in Master.xml...")
    udf_tags = set(re.findall(r'<(UDF:[^>]*CORS[^>]*)>', content, re.IGNORECASE))
    print("Found UDF tags containing 'CORS':", udf_tags)

search_cors_udfs()
