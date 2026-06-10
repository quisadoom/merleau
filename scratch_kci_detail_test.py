import urllib.request
import urllib.parse
API_KEY = "53654818"
URL = f"https://open.kci.go.kr/po/openapi/openApiSearch.kci?apiCode=articleDetail&key={API_KEY}&id=ART003094597"
req = urllib.request.Request(URL)
try:
    with urllib.request.urlopen(req) as response:
        xml_data = response.read().decode('utf-8')
        with open("c:/dashboard/scratch_kci_detail.xml", "w", encoding="utf-8") as f:
            f.write(xml_data)
        print("Detail response saved")
except Exception as e:
    print(f"Error: {e}")
