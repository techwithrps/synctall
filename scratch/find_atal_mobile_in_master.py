import re

def search_atal_mobile():
    with open("Master.xml", "rb") as f:
        content = f.read().decode("utf-16")
        
    print("Searching for Atal mobile 6909762639 in Master.xml...")
    pattern = r'<([^>]+)>([^<]*6909762639[^<]*)</\1>'
    matches = re.findall(pattern, content)
    print("Matches for 6909762639:", matches)
    
    print("Searching for another mobile 8580527177 in Master.xml...")
    pattern2 = r'<([^>]+)>([^<]*8580527177[^<]*)</\1>'
    matches2 = re.findall(pattern2, content)
    print("Matches for 8580527177:", matches2)

search_atal_mobile()
