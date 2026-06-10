import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

API_KEY = "53654818"
encoded_query = urllib.parse.quote("메를로-퐁티")
URL = f"https://open.kci.go.kr/po/openapi/openApiSearch.kci?apiCode=articleSearch&key={API_KEY}&title={encoded_query}&displayCount=2"

req = urllib.request.Request(URL)
try:
    with urllib.request.urlopen(req) as response:
        xml_data = response.read().decode('utf-8')
        with open("c:/dashboard/scratch_kci_response.xml", "w", encoding="utf-8") as f:
            f.write(xml_data)
        print("Response saved to scratch_kci_response.xml")
except Exception as e:
    print(f"Error: {e}")
