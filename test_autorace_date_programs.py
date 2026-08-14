import re
import sys
import urllib.request

DATES = ["2026-08-15", "2026-08-16"]

VENUES = {
    "川口": "kawaguchi",
    "伊勢崎": "isesaki",
    "浜松": "hamamatsu",
    "飯塚": "iizuka",
    "山陽": "sanyo",
}

BASES = [
    "https://autorace.jp/race_info/Program/Print/{slug}/{date}",
    "https://autorace.jp/race_info/Program/Web/{slug}/{date}_1",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
}

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

def plain(src):
    src = re.sub(r"(?is)<script.*?</script>", " ", src)
    src = re.sub(r"(?is)<style.*?</style>", " ", src)
    src = re.sub(r"(?s)<[^>]+>", " ", src)
    return re.sub(r"\s+", " ", src)

def parse_times(src):
    s = plain(src)
    found = {}
    patterns = [
        r"(\d{1,2})\s*R.{0,100}?発走(?:予定時刻)?\s*[:：]?\s*([0-2]?\d:[0-5]\d)",
        r"(\d{1,2})\s*R.{0,100}?\(発走\s*([0-2]?\d:[0-5]\d)\)",
        r"(\d{1,2})\s*R.{0,80}?([0-2]?\d:[0-5]\d)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, s, re.S | re.I):
            rn = int(m.group(1))
            if 1 <= rn <= 12:
                tm = m.group(2)
                if len(tm) == 4:
                    tm = "0" + tm
                found[rn] = tm
        if len(found) >= 5:
            break
    return [(n, found[n]) for n in sorted(found)]

def main():
    print("AUTORACE DATE-SPECIFIC PROGRAM TEST")
    print()

    for date in DATES:
        print("=" * 72)
        print(date)
        print("=" * 72)

        for venue, slug in VENUES.items():
            best = []
            status = "NO DATA"

            for template in BASES:
                url = template.format(slug=slug, date=date)
                try:
                    src = fetch(url)
                except Exception as e:
                    print(f"{venue}: {url} -> {type(e).__name__}")
                    continue

                races = parse_times(src)
                if len(races) > len(best):
                    best = races

                p = plain(src)
                if date in p or date.replace("-", "/") in p:
                    status = "DATE PAGE EXISTS"

            if best:
                print(f"{venue}: {len(best)}R  " + " / ".join(f"{r}R {t}" for r,t in best))
            else:
                print(f"{venue}: {status}")

        print()

    print("TEST FINISHED")
    sys.exit(0)

if __name__ == "__main__":
    main()
