import xml.etree.ElementTree as ET
import re

def search_xml(file_path):
    print(f"Searching: {file_path}")
    try:
        # Read file with correct encoding (UTF-16LE or UTF-8)
        try:
            with open(file_path, "r", encoding="utf-16le") as f:
                content = f.read()
        except UnicodeError:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        
        # Strip XML declaration if it has encoding mismatch
        content_clean = re.sub(r'<\?xml.*?\?>', '', content, flags=re.IGNORECASE)
        
        # Look for any occurrence of 'ShlOl' or token/code/company keys
        lines = content_clean.split("\n")
        print(f"Total lines: {len(lines)}")
        
        # Search lines
        matches = 0
        for i, line in enumerate(lines):
            if any(term in line.lower() for term in ["shlol", "token", "companycode", "company_code", "company id", "elogipay"]):
                print(f"Line {i+1}: {line.strip()}")
                matches += 1
                if matches > 30:
                    print("Too many matches, truncating...")
                    break
        if matches == 0:
            print("No matches found.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    search_xml("Master.xml")
    print("-" * 50)
    search_xml("Transactions.xml.processed")
