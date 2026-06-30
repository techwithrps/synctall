with open("Master.xml", "rb") as f:
    content = f.read().decode("utf-16")

print("Searching for 'Papu' in Master.xml...")
idx = 0
while True:
    idx = content.find("Papu", idx)
    if idx == -1:
        break
    print(f"\nFound 'Papu' at index {idx}:")
    print(content[max(0, idx-200):min(len(content), idx+200)])
    idx += 4
    break  # just print the first one
