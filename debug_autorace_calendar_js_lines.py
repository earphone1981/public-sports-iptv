import sys
import urllib.request

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

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        print("HTTP", r.status, url)
    return raw.decode("utf-8", errors="ignore")

def main():
    src = fetch(URL)
    lines = src.splitlines()

    start = 220
    end = 250

    print()
    print("=" * 80)
    print(f"calendar.js lines {start}-{end}")
    print("=" * 80)

    for i in range(start, min(end, len(lines)) + 1):
        print(f"{i}: {lines[i-1]}")

    print()
    print("END")
    sys.exit(0)

if __name__ == "__main__":
    main()
