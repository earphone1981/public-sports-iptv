import html
import re
import sys
import urllib.request

DATES = {
    "20260815": "05",
    "20260816": "06",
}

BASE = "https://keirin.kdreams.jp"
EVENT = "7520260811"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.7,en;q=0.6",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read()
        print(f"HTTP {res.status}: {url}")

    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            return body.decode(enc)
        except Exception:
            pass

    return body.decode("utf-8", errors="ignore")


def clean_text(src):
    src = re.sub(r"(?is)<script.*?</script>", " ", src)
    src = re.sub(r"(?is)<style.*?</style>", " ", src)
    src = re.sub(r"(?s)<[^>]+>", " ", src)
    src = html.unescape(src)
    return re.sub(r"\s+", " ", src).strip()


def parse_races(src):
    plain = clean_text(src)
    races = {}

    patterns = [
        re.compile(
            r"(\d{1,2})R\s*(.*?)\s*発走(?:予定)?\s*[:：]?\s*([0-2]?\d:[0-5]\d)",
            re.S
        ),
        re.compile(
            r"(\d{1,2})R\s*(.*?)\s*発走\s*([0-2]?\d:[0-5]\d)",
            re.S
        ),
    ]

    for pat in patterns:
        for m in pat.finditer(plain):
            rn = int(m.group(1))
            if 1 <= rn <= 12:
                name = re.sub(r"\s+", " ", m.group(2)).strip()
                if len(name) > 80:
                    name = name[:80] + "..."
                hhmm = m.group(3)
                if len(hhmm) == 4:
                    hhmm = "0" + hhmm
                races[rn] = (hhmm, name)
        if len(races) >= 5:
            break

    return [(rn, *races[rn]) for rn in sorted(races)]


def main():
    ok = True

    for date_str, day_no in DATES.items():
        # KDreams/Gamboo URL convention:
        # EVENT + day_no + "00"
        day_id = f"{EVENT}{day_no}00"

        urls = [
            f"{BASE}/matsuyama/racecard/{day_id}/",
            f"{BASE}/gamboo/keirin-kaisai/race-program/{EVENT}/{day_id}/",
            f"{BASE}/yenjoy/keirin-kaisai/race-program/{EVENT}/{day_id}/",
        ]

        print()
        print("=" * 72)
        print("KDREAMS FUTURE TEST:", date_str, day_id)
        print("=" * 72)

        best = []

        for url in urls:
            try:
                src = fetch(url)
            except Exception as e:
                print("FETCH FAILED:", repr(e))
                continue

            races = parse_races(src)
            print("RACES FOUND:", len(races))

            if len(races) > len(best):
                best = races

            if len(races) >= 5:
                for rn, tm, name in races:
                    print(f"{rn:>2}R {tm} {name}")
                break

        if not best:
            print("NO RACE TIMES FOUND")
            ok = False
        else:
            print("BEST COUNT:", len(best))

    print()
    if ok:
        print("KDREAMS FUTURE TEST OK")
        sys.exit(0)
    else:
        print("KDREAMS FUTURE TEST FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
