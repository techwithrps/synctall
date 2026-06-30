import socket
import urllib.parse
import requests

tally_url = "http://103.107.67.58:9631/"
print(f"Testing connection to Tally URL: {tally_url}")

# Parse URL
url_parts = urllib.parse.urlparse(tally_url)
host = url_parts.hostname
port = url_parts.port

print(f"Host: {host}, Port: {port}")

# Test TCP socket connection
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    result = sock.connect_ex((host, port))
    sock.close()
    if result == 0:
        print("TCP socket connection: SUCCESS (Port is open!)")
    else:
        print(f"TCP socket connection: FAILED (connect_ex returned code {result})")
except Exception as e:
    print(f"TCP socket connection error: {e}")

# Test HTTP POST request
payload = """<ENVELOPE>
 <HEADER>
  <VERSION>1</VERSION>
  <TALLYREQUEST>EXPORT</TALLYREQUEST>
  <TYPE>COLLECTION</TYPE>
  <ID>Ledger</ID>
 </HEADER>
 <BODY>
  <DESC>
   <STATICVARIABLES>
    <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
   </STATICVARIABLES>
  </DESC>
 </BODY>
</ENVELOPE>"""

try:
    response = requests.post(tally_url, data=payload, headers={"Content-Type": "text/xml; charset=utf-8"}, timeout=5)
    print(f"HTTP Response Status Code: {response.status_code}")
    print(f"HTTP Response Content: {response.text[:500]}")
except Exception as e:
    print(f"HTTP Request error: {e}")
