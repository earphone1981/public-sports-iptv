import json
import urllib.parse
import urllib.request

API = "https://autorace.jp/race_info/XML/Calendar"
MONTH = "2026-08"
TARGET_DATES = {"2026-08-15", "2026-08-16", "20260815", "20260816"}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://autorace.jp/calendar/",
    "Accept": "application/json,text/javascript,*/*;q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

url = API + "?" + urllib.parse.urlencode({"date": MONTH})
req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req, timeout=30) as r:
    raw = r.read()
    print("HTTP:", r.status)
    print("URL:", r.geturl())

text = raw.decode("utf-8", errors="replace")
data = json.loads(text)

print("\n===== JSON TYPE =====")
print(type(data).__name__)

print("\n===== TARGET DATE MATCHES =====")

def walk(obj, path="root"):
    if isinstance(obj, dict):
        blob = json.dumps(obj, ensure_ascii=False)
        if any(d in blob for d in TARGET_DATES):
            print("\nPATH:", path)
            print(json.dumps(obj, ensure_ascii=False, indent=2)[:12000])
        for k, v in obj.items():
            walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")

walk(data)

print("\n===== JSON PREVIEW =====")
print(json.dumps(data, ensure_ascii=False, indent=2)[:20000])
