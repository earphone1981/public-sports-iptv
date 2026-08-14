import re
import sys
import urllib.request
from urllib.parse import urljoin

URL = "https://autorace.jp/content/assets/js/calendar.js"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

KEYS = [
    "api", "json", "calendar", "schedule", "ajax", "fetch", "axios",
    "url:", "$.get", "$.ajax", "race", "kaisai", "grade",
    "morning", "night", "midnight", "over", "開催", "ミッドナイト",
]

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        print("HTTP", r.status, url)
        print("Content-Type:", r.headers.get("Content-Type", ""))
        print("Bytes:", len(raw))
    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="ignore")

def extract_urls(src):
    found = set()
    patterns = [
        r'["\']([^"\']+\.json(?:\?[^"\']*)?)["\']',
        r'["\']([^"\']*(?:api|calendar|schedule|race|kaisai)[^"\']*)["\']',
        r'fetch\(\s*["\']([^"\']+)["\']',
        r'axios\.(?:get|post)\(\s*["\']([^"\']+)["\']',
        r'\$\.get(?:JSON)?\(\s*["\']([^"\']+)["\']',
        r'url\s*:\s*["\']([^"\']+)["\']',
    ]
    for pat in patterns:
        for m in re.finditer(pat, src, flags=re.I | re.S):
            v = m.group(1).strip()
            if not v or v.startswith("data:") or v.startswith("javascript:"):
                continue
            found.add(urljoin(URL, v))
    return sorted(found)

def main():
    src = fetch(URL)

    print()
    print("=" * 90)
    print("CALENDAR.JS INTERESTING LINES")
    print("=" * 90)

    for i, line in enumerate(src.splitlines(), start=1):
        low = line.lower()
        if any(k.lower() in low for k in KEYS):
            print(f"{i}: {line[:1600]}")

    print()
    print("=" * 90)
    print("CANDIDATE ENDPOINTS")
    print("=" * 90)
    urls = extract_urls(src)
    for u in urls:
        print(u)

    print()
    print("=" * 90)
    print("DATE / PARAMETER PATTERNS")
    print("=" * 90)

    pats = [
        r'year',
        r'month',
        r'day',
        r'yyyy',
        r'mm',
        r'dd',
        r'param',
        r'data:',
        r'query',
    ]
    for i, line in enumerate(src.splitlines(), start=1):
        low = line.lower()
        if any(re.search(p, low) for p in pats):
            print(f"{i}: {line[:1600]}")

    print()
    print("CALENDAR.JS DEBUG END")
    sys.exit(0)

if __name__ == "__main__":
    main()
