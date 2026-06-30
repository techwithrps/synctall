import re

def search_email_in_master():
    encodings = ['utf-16', 'utf-8', 'latin1']
    content = None
    for enc in encodings:
        try:
            print(f"Trying encoding: {enc}")
            with open("Master.xml", "rb") as f:
                content = f.read().decode(enc)
            print(f"Successfully decoded with {enc}")
            break
        except Exception as e:
            print(f"Failed with {enc}: {e}")
            
    if not content:
        print("Could not read Master.xml")
        return
        
    print("Searching for email addresses or email tags in Master.xml...")
    # Find tag name with email value
    matches = re.findall(r'<([^>]+)>([^<]+@[^<]+)</\1>', content)
    if matches:
        print(f"Found {len(matches)} matches:")
        # Print unique tag names
        tags = set()
        for tag, val in matches:
            tags.add(tag)
            if len(tags) < 10:
                print(f"  <{tag}>: {val}")
        print("Unique tags with email values:", tags)
    else:
        print("No email values found.")
        
    # Search for EMAL or EMAIL or similar tags
    print("Searching for EMAL or EMAIL tags...")
    matches_tags = re.findall(r'<[^>]*email[^>]*>', content, re.IGNORECASE)
    print("Found tags containing 'email':", set(matches_tags))
    
    matches_emal = re.findall(r'<[^>]*emal[^>]*>', content, re.IGNORECASE)
    print("Found tags containing 'emal':", set(matches_emal))

search_email_in_master()
