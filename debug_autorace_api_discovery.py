import re
import sys
import urllib.request
from urllib.parse import urljoin

URLS = [
    "https://autorace.jp/calendar/",
    "https://autorace.jp/calendar/graderace/",
]

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
        print("Content-Type:", r.headers.get("Content-Type", ""))
        print("Bytes:", len(raw))
    for enc in ("utf-8", "cp932", "shift_jis", "euc_jp"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="ignore")

def extract_candidates(base_url, src):
    found = set()
    patterns = [
        r'(?:src|href)=["\']([^"\']+\.(?:js|json)(?:\?[^"\']*)?)["\']',
        r'["\']([^"\']*(?:api|calendar|schedule|race)[^"\']*\.(?:js|json)(?:\?[^"\']*)?)["\']',
        r'fetch\(\s*["\']([^"\']+)["\']\s*\)',
        r'axios\.(?:get|post)\(\s*["\']([^"\']+)["\']',
        r'\$\.get(?:JSON)?\(\s*["\']([^"\']+)["\']',
        r'url\s*:\s*["\']([^"\']+)["\']',
    ]

    for pat in patterns:
        for m in re.finditer(pat, src, flags=re.I | re.S):
            val = m.group(1).strip()
            if val.startswith("data:") or val.startswith("javascript:"):
                continue
            found.add(urljoin(base_url, val))
    return sorted(found)

def interesting_lines(src):
    keys = [
        "calendar", "schedule", "api", "json", "ajax", "fetch(",
        "axios", "$.get", "$.ajax", "race", "kaisai", "開催",
    ]
    out = []
    for i, line in enumerate(src.splitlines(), start=1):
        low = line.lower()
        if any(k.lower() in low for k in keys):
            out.append((i, line.strip()))
    return out

def main():
    all_candidates = []

    for url in URLS:
        print()
        print("=" * 90)
        print("PAGE:", url)
        print("=" * 90)

        try:
            src = fetch(url)
        except Exception as e:
            print("FETCH FAILED:", repr(e))
            continue

        print()
        print("===== CANDIDATE URLS =====")
        candidates = extract_candidates(url, src)
        for c in candidates:
            print(c)
            all_candidates.append(c)

        print()
        print("===== INTERESTING HTML/JS LINES =====")
        for no, line in interesting_lines(src)[:500]:
            print(f"{no}: {line[:1200]}")

    print()
    print("=" * 90)
    print("UNIQUE CANDIDATES:", len(set(all_candidates)))
    print("=" * 90)
    for c in sorted(set(all_candidates)):
        print(c)

    print()
    print("AUTORACE API DISCOVERY DEBUG END")
    sys.exit(0)

if __name__ == "__main__":
    main()
