import html
import re
import sys
import urllib.error
import urllib.request
import http.cookiejar

TARGET_DATE = "20260815"
URL = "https://www.jra.go.jp/keiba/calendar2026/2026/8/0815.html"

VENUE_TO_STREAM = {
    "東京": "JRA EAST",
    "中山": "JRA EAST",
    "新潟": "JRA EAST",
    "福島": "JRA EAST",
    "京都": "JRA WEST",
    "阪神": "JRA WEST",
    "中京": "JRA WEST",
    "小倉": "JRA WEST",
    "札幌": "JRA HOKKAIDO",
    "函館": "JRA HOKKAIDO",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.7,en;q=0.6",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}


def fetch(opener, url, referer=None):
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer

    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=30) as res:
        print("HTTP:", res.status, res.geturl())
        return res.read().decode("utf-8", errors="ignore")


def strip_html_tags(source):
    source = re.sub(r"(?is)<script.*?</script>", " ", source)
    source = re.sub(r"(?is)<style.*?</style>", " ", source)
    source = re.sub(r"(?s)<[^>]+>", " ", source)
    source = html.unescape(source)
    return re.sub(r"\s+", " ", source).strip()


def parse_calendar(source):
    plain = strip_html_tags(source)
    venues = list(VENUE_TO_STREAM)
    out = {}

    # Locate each race-meeting heading, then stop at the next meeting heading.
    heading_re = re.compile(
        r"(\d+)回(東京|中山|新潟|福島|京都|阪神|中京|小倉|札幌|函館)(\d+)日"
    )
    headings = list(heading_re.finditer(plain))

    for i, m in enumerate(headings):
        venue = m.group(2)
        start = m.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(plain)
        section = plain[start:end]

        races = []
        race_re = re.compile(
            r"(\d{1,2})レース\s+(.*?)\s+([0-2]?\d)時([0-5]\d)分",
            flags=re.S,
        )
        for rm in race_re.finditer(section):
            race_no = int(rm.group(1))
            if not 1 <= race_no <= 12:
                continue

            name = re.sub(r"\s+", " ", rm.group(2)).strip()
            races.append({
                "race": race_no,
                "time": f"{int(rm.group(3)):02d}:{rm.group(4)}",
                "name": name[:140],
            })

        # De-duplicate by race number.
        dedup = {r["race"]: r for r in races}
        races = [dedup[n] for n in sorted(dedup)]
        if races:
            out[venue] = races

    return out


def main():
    print("JRA TEST:", TARGET_DATE)
    print("URL:", URL)

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)
    )

    try:
        # Prime cookies / session first.
        try:
            fetch(opener, "https://www.jra.go.jp/", referer="https://www.google.com/")
            print("JRA top page: OK")
        except Exception as e:
            print("JRA top page: failed:", repr(e))

        source = fetch(opener, URL, referer="https://www.jra.go.jp/keiba/calendar/")
    except urllib.error.HTTPError as e:
        print("FAILED: HTTP", e.code, e.reason)
        sys.exit(2)
    except Exception as e:
        print("FAILED:", repr(e))
        sys.exit(3)

    meetings = parse_calendar(source)

    print()
    print("===== RESULT =====")
    if not meetings:
        print("NO MEETINGS PARSED")
        sys.exit(4)

    streams = {"JRA EAST": [], "JRA WEST": [], "JRA HOKKAIDO": []}

    for venue, races in meetings.items():
        stream = VENUE_TO_STREAM.get(venue, "UNKNOWN")
        streams.setdefault(stream, []).append(venue)
        print(f"{venue}: {len(races)} races -> {stream}")
        for r in races:
            print(f"  {r['race']:>2}R {r['time']} {r['name']}")

    print()
    print("===== STREAM MAP =====")
    for stream in ("JRA EAST", "JRA WEST", "JRA HOKKAIDO"):
        names = " / ".join(streams.get(stream, [])) or "0"
        print(f"{stream}: {names}")

    # 2026-08-15 official programme should have these three venues.
    expected = {"新潟", "中京", "札幌"}
    missing = expected - set(meetings)
    if missing:
        print("WARNING: expected venue(s) missing:", ", ".join(sorted(missing)))
        sys.exit(5)

    print()
    print("JRA TEST OK")


if __name__ == "__main__":
    main()
