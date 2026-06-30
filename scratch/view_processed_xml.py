import sys

def main():
    try:
        with open('Transactions.xml.processed', 'r', encoding='utf-16') as f:
            lines = f.readlines()
        
        start = 200
        end = 350
        print(f"Total lines: {len(lines)}")
        print(f"Showing lines {start} to {end}:")
        for i in range(start, min(end, len(lines))):
            print(f"{i+1}: {lines[i]}", end="")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
