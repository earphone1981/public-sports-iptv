import html
import re
import sys
import urllib.request

DATES = ["20260815", "20260816"]

VENUES = {
    "川口": "kawaguchi",
    "伊勢崎": "isesaki",
    "浜松": "hamamatsu",
    "飯塚": "iizuka",
    "山陽": "sanyo",
}

URLS = [
    "https://autorace.jp/race_info/Live/{slug}",
    "https://autorace.jp/race_info/Program/{slug}",
    "https://autorace.jp/race_info/{slug}",
]

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
        print("HTTP", res.status, url)

    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            return body.decode(enc)
        except Exception:
            pass
    return body.decode("utf-8", errors="ignore")


def strip_html(src):
    src = re.sub(r"(?is)<script.*?</script>", " ", src)
    src = re.sub(r"(?is)<style.*?</style>", " ", src)
    src = re.sub(r"(?s)<[^>]+>", " ", src)
    src = html.unescape(src)
    return re.sub(r"\s+", " ", src).strip()


def parse_times(source):
    plain = strip_html(source)
    races = {}

    patterns = [
        re.compile(r"\b(\d{1,2})R\b.{0,120}?([0-2]?\d:[0-5]\d)", re.S),
        re.compile(r"(\d{1,2})\s*R.{0,120}?発走.{0,30}?([0-2]?\d:[0-5]\d)", re.S),
        re.compile(r"(\d{1,2})\s*レース.{0,120}?([0-2]?\d:[0-5]\d)", re.S),
    ]

    for pat in patterns:
        for m in pat.finditer(plain):
            rn = int(m.group(1))
            if 1 <= rn <= 12:
                hhmm = m.group(2)
                if len(hhmm) == 4:
                    hhmm = "0" + hhmm
                races[rn] = hhmm
        if len(races) >= 5:
            break

    return [(rn, races[rn]) for rn in sorted(races)]


def main():
    print("AUTORACE FUTURE TEST")
    print("This test first checks whether official venue pages already expose future race times.")
    print()

    # Current/future venue pages are not date-addressable in the obvious URLs,
    # so this test records what the official pages expose now and checks for
    # date strings 20260815 / 20260816 in the source.
    any_future = False

    for venue, slug in VENUES.items():
        print()
        print("=" * 70)
        print(venue)
        print("=" * 70)

        best = []

        for tpl in URLS:
            url = tpl.format(slug=slug)

            try:
                source = fetch(url)
            except Exception as e:
                print("FETCH FAILED:", repr(e))
                continue

            plain = strip_html(source)

            future_hits = []
            for date_str in DATES:
                variants = [
                    date_str,
                    f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}",
                    f"{int(date_str[4:6])}月{int(date_str[6:])}日",
                ]
                if any(v in plain for v in variants):
                    future_hits.append(date_str)

            races = parse_times(source)
            print("FUTURE DATE HITS:", ",".join(future_hits) if future_hits else "none")
            print("RACES FOUND:", len(races))

            if races:
                print("  " + " / ".join(f"{rn}R {tm}" for rn, tm in races))

            if len(races) > len(best):
                best = races

            if future_hits and races:
                any_future = True

    print()
    print("=" * 70)
    if any_future:
        print("OFFICIAL SITE EXPOSES FUTURE RACE TIMES")
        sys.exit(0)

    print("NO DATE-ADDRESSED FUTURE RACE TIMES FOUND ON OFFICIAL VENUE PAGES")
    print("Next fallback should be future schedule metadata + provisional time blocks.")
    sys.exit(0)


if __name__ == "__main__":
    main()
