import re

def search_any_address():
    with open("Master.xml", "rb") as f:
        content = f.read().decode("utf-16")
        
    print("Searching for address text in UDFs...")
    # Find all UDF lists and print their names and values
    # UDF list format is usually <UDF:UDF_NAME.LIST ...> <UDF:UDF_NAME ...> value </UDF:UDF_NAME> </UDF:UDF_NAME.LIST>
    udfs = re.findall(r'<UDF:([^.]+)\.LIST[^>]*>.*?<UDF:\1[^>]*>(.*?)</UDF:\1>.*?Multiplier', content, re.DOTALL)
    print(f"Found {len(udfs)} UDFs in Master.xml.")
    
    # Let's search for typical address words in the UDF values
    address_keywords = ["nallah", "dist", "kameng", "seppa", "solan", "himachal", "pradesh", "road", "street", "house", "village", "tehsil", "post"]
    found_count = 0
    for udf_name, udf_val in udfs:
        val_lower = udf_val.lower()
        if any(kw in val_lower for kw in address_keywords):
            print(f"UDF {udf_name} contains address keyword: {udf_val}")
            found_count += 1
            if found_count > 10:
                break

search_any_address()
