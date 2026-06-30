import sys
import xml.etree.ElementTree as ET

sys.path.append("/Users/twrps/Desktop/synctal")

from sync_agent.tally_client import TallyClient

print("Fetching XML from Tally...")
client = TallyClient()
xml_data = client.fetch_student_details()

print("XML fetched. Length:", len(xml_data))

# Let's save a copy of the XML to scratch for debugging
with open("/Users/twrps/Desktop/synctal/scratch/tally_response.xml", "w", encoding="utf-8") as f:
    f.write(xml_data)
print("Saved XML to scratch/tally_response.xml")

# Let's search for "102" in the XML data
if "102" in xml_data:
    print("Found '102' in raw XML!")
    # Let's print around the match
    idx = xml_data.find("102")
    start = max(0, idx - 200)
    end = min(len(xml_data), idx + 200)
    print("Context:")
    print(xml_data[start:end])
else:
    print("Did NOT find '102' in raw XML!")
