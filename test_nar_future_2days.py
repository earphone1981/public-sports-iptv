import html
import re
import sys
import urllib.parse
import urllib.request

DATES = ["20260815", "20260816"]

VENUE_CODES = {
    "帯広": "03",
    "盛岡": "10",
    "水沢": "11",
    "浦和": "18",
    "船橋": "19",
    "大井": "20",
    "川崎": "21",
    "金沢": "22",
    "笠松": "23",
    "名古屋": "24",
    "園田": "27",
    "姫路": "28",
    "高知": "31",
    "佐賀": "32",
    "門別": "36",
}

URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList"
    "?k_babaCode={code}&k_raceDate={date}"
)

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


def parse_races(source):
    plain = strip_html(source)
    races = {}

    # NAR page visible rows look like:
    # 1R 15:40 ... race name ...
    row_re = re.compile(
        r"\b(\d{1,2})R\b\s+([0-2]?\d:[0-5]\d)\s+(.*?)(?=\s+\d{1,2}R\s+[0-2]?\d:[0-5]\d|\s+重賞競走優勝馬検索|\Z)",
        flags=re.S,
    )

    for m in row_re.finditer(plain):
        rn = int(m.group(1))
        if not 1 <= rn <= 12:
            continue

        hhmm = m.group(2)
        if len(hhmm) == 4:
            hhmm = "0" + hhmm

        tail = re.sub(r"\s+", " ", m.group(3)).strip()

        # Remove common trailing columns after race name as much as possible.
        name = re.split(
            r"\s+(?:右|左|直線)\d+m|\s+オッズ\b|\s+映像\b|\s+成績\b",
            tail,
            maxsplit=1,
        )[0].strip()

        # Remove leading race type labels if present but keep useful labels.
        name = name[:160]

        races[rn] = {
            "race": str(rn),
            "time": hhmm,
            "name": name,
        }

    return [races[n] for n in sorted(races)]


def main():
    all_ok = True

    for date_str in DATES:
        yyyy = date_str[:4]
        mm = date_str[4:6]
        dd = date_str[6:8]
        date_param = f"{yyyy}/{mm}/{dd}"

        print()
        print("=" * 72)
        print("NAR FUTURE TEST:", date_str)
        print("=" * 72)

        found = {}

        for venue, code in VENUE_CODES.items():
            url = URL.format(
                code=code,
                date=urllib.parse.quote(date_param, safe=""),
            )

            try:
                source = fetch(url)
            except Exception as e:
                print(f"{venue}: FETCH FAILED {e!r}")
                continue

            plain = strip_html(source)

            # Reject pages that don't identify this venue/date as an actual menu.
            if venue not in plain or "当日メニュー" not in plain:
                continue

            races = parse_races(source)
            if not races:
                continue

            found[venue] = races

            print()
            print(f"{venue}: {len(races)}R")
            print(
                "  "
                + " / ".join(
                    f"{r['race']}R {r['time']} {r['name']}"
                    for r in races
                )
            )

        print()
        print("VENUES FOUND:", len(found))
        print(" / ".join(found) if found else "NONE")

        if not found:
            all_ok = False

    print()
    if all_ok:
        print("NAR FUTURE 2-DAY TEST OK")
        sys.exit(0)

    print("NAR FUTURE 2-DAY TEST FAILED")
    sys.exit(1)


if __name__ == "__main__":
    main()
