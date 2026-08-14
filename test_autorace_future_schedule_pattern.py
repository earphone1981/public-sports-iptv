import re
import sys
import urllib.request

DATES = ["20260815", "20260816"]

# AutoRace venues
VENUES = ["川口", "伊勢崎", "浜松", "飯塚", "山陽"]

# We deliberately inspect multiple official schedule/calendar pages because
# AutoRace.JP separates ordinary schedules and graded-race information.
URLS = [
    "https://autorace.jp/calendar/",
    "https://autorace.jp/calendar/graderace/",
    "https://autorace.jp/",
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

PATTERNS = [
    ("オーバーミッドナイト", "🌑"),
    ("ミッドナイト", "⭐"),
    ("モーニング", "🌅"),
    ("ナイター", "🌙"),
]

GRADES = ["SG", "G1", "G2"]

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        print("HTTP", r.status, url)
    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="ignore")

def clean(src):
    src = re.sub(r"(?is)<script.*?</script>", " ", src)
    src = re.sub(r"(?is)<style.*?</style>", " ", src)
    src = re.sub(r"(?s)<[^>]+>", " ", src)
    src = re.sub(r"&nbsp;|&#160;", " ", src)
    return re.sub(r"\s+", " ", src).strip()

def date_variants(ds):
    y, m, d = ds[:4], int(ds[4:6]), int(ds[6:8])
    return [
        ds,
        f"{y}/{m:02d}/{d:02d}",
        f"{y}-{m:02d}-{d:02d}",
        f"{m}/{d}",
        f"{m:02d}/{d:02d}",
        f"{m}月{d}日",
        f"{m:02d}月{d:02d}日",
    ]

def classify(context):
    pattern = ("デイ", "☀️")
    for name, emoji in PATTERNS:
        if name in context:
            pattern = (name, emoji)
            break

    grade = "普通開催"
    for g in GRADES:
        if re.search(rf"(?<![A-Z0-9]){re.escape(g)}(?![A-Z0-9])", context, re.I):
            grade = g
            break

    return grade, pattern[0], pattern[1]

def main():
    pages = []
    for url in URLS:
        try:
            src = fetch(url)
            pages.append((url, clean(src)))
        except Exception as e:
            print("FETCH FAILED", url, repr(e))

    print()
    print("=" * 78)
    print("AUTORACE FUTURE SCHEDULE / PATTERN TEST")
    print("Patterns: 🌅モーニング / ☀️デイ / 🌙ナイター / ⭐ミッドナイト / 🌑オーバーミッドナイト")
    print("=" * 78)

    for ds in DATES:
        print()
        print("DATE:", ds)
        found = {}

        for url, text in pages:
            variants = date_variants(ds)

            for venue in VENUES:
                # Search venue occurrences and inspect a wide surrounding window.
                for vm in re.finditer(re.escape(venue), text):
                    a = max(0, vm.start() - 500)
                    b = min(len(text), vm.end() + 900)
                    ctx = text[a:b]

                    if not any(v in ctx for v in variants):
                        continue

                    grade, pattern, emoji = classify(ctx)
                    found.setdefault(venue, {
                        "grade": grade,
                        "pattern": pattern,
                        "emoji": emoji,
                        "source": url,
                    })

        if not found:
            print("  NO FUTURE MEETINGS DETECTED")
            continue

        for venue, info in found.items():
            print(
                f"  {venue}: [{info['grade']}] "
                f"{info['emoji']}{info['pattern']} "
                f"source={info['source']}"
            )

    print()
    print("TEST FINISHED")
    sys.exit(0)

if __name__ == "__main__":
    main()
