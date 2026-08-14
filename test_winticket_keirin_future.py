import html
import re
import sys
import urllib.request
import urllib.error

DATES = ["20260815", "20260816"]

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

BASE = "https://www.winticket.jp"

VENUE_CODE = {
    "11": "函館", "12": "青森", "13": "いわき平", "21": "弥彦",
    "22": "前橋", "23": "取手", "24": "宇都宮", "25": "大宮",
    "26": "西武園", "27": "京王閣", "28": "立川", "31": "松戸",
    "32": "千葉", "34": "川崎", "35": "平塚", "36": "小田原",
    "37": "伊東", "38": "静岡", "41": "一宮", "42": "名古屋",
    "43": "岐阜", "44": "大垣", "45": "豊橋", "46": "富山",
    "47": "松阪", "48": "四日市", "51": "福井", "53": "奈良",
    "54": "向日町", "55": "和歌山", "56": "岸和田", "61": "玉野",
    "62": "広島", "63": "防府", "71": "高松", "73": "小松島",
    "74": "高知", "75": "松山", "81": "小倉", "83": "久留米",
    "84": "武雄", "85": "佐世保", "86": "別府", "87": "熊本",
}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read()
        ctype = res.headers.get("Content-Type", "")
        print(f"HTTP {res.status}: {url}")

    # WINTICKET is normally UTF-8, but keep a small fallback.
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


def discover_meetings(date_str):
    """
    Discover race meeting URLs from the WINTICKET daily racecard page.
    We deliberately discover links instead of hardcoding venue URLs.
    """
    daily_url = f"{BASE}/keirin/racecard/{date_str}"
    source = fetch(daily_url)

    # Examples seen on WINTICKET:
    # /keirin/matsuyama/racecard/2026072575/races
    pat = re.compile(
        rf'href=["\'](?P<href>/keirin/(?P<slug>[^/"\']+)/racecard/'
        rf'{date_str}(?P<code>\d{{2}})/races(?:[^"\']*)?)["\']',
        flags=re.I,
    )

    found = {}
    for m in pat.finditer(source):
        code = m.group("code")
        href = html.unescape(m.group("href"))
        found[code] = {
            "code": code,
            "slug": m.group("slug"),
            "url": BASE + href.split("?")[0],
            "venue": VENUE_CODE.get(code, m.group("slug")),
        }

    # Fallback: sometimes the page may contain absolute URLs.
    if not found:
        pat2 = re.compile(
            rf'https://www\.winticket\.jp/keirin/(?P<slug>[^/"\']+)/racecard/'
            rf'{date_str}(?P<code>\d{{2}})/races',
            flags=re.I,
        )
        for m in pat2.finditer(source):
            code = m.group("code")
            found[code] = {
                "code": code,
                "slug": m.group("slug"),
                "url": m.group(0),
                "venue": VENUE_CODE.get(code, m.group("slug")),
            }

    return [found[k] for k in sorted(found)]


def parse_races(source):
    plain = clean_text(source)
    races = {}

    # Common visible format: "1R 発走 10:57"
    patterns = [
        re.compile(r"\b(\d{1,2})R\b.{0,100}?発走\s*([0-2]?\d:[0-5]\d)", re.S),
        re.compile(r"\b(\d{1,2})R\b.{0,100}?([0-2]?\d:[0-5]\d)\s*発走", re.S),
        re.compile(r"(\d{1,2})\s*R.{0,120}?([0-2]?\d:[0-5]\d)", re.S),
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
    all_ok = True

    for date_str in DATES:
        print()
        print("=" * 64)
        print(f"WINTICKET KEIRIN TEST: {date_str}")
        print("=" * 64)

        try:
            meetings = discover_meetings(date_str)
        except Exception as e:
            print("DAILY PAGE FAILED:", repr(e))
            all_ok = False
            continue

        print(f"MEETINGS FOUND: {len(meetings)}")

        if not meetings:
            print("No meeting URLs found on daily page.")
            all_ok = False
            continue

        for meeting in meetings:
            print()
            print(
                f"[{meeting['code']}] {meeting['venue']} "
                f"({meeting['slug']})"
            )
            print(meeting["url"])

            try:
                source = fetch(meeting["url"])
                races = parse_races(source)
            except Exception as e:
                print("  FETCH FAILED:", repr(e))
                all_ok = False
                continue

            if not races:
                print("  RACES: 0  <-- parse failed / not published yet")
                all_ok = False
                continue

            print(f"  RACES: {len(races)}")
            print("  " + " / ".join(f"{rn}R {tm}" for rn, tm in races))

        # Easy checkpoint for this test period.
        matsuyama = [x for x in meetings if x["code"] == "75"]
        if matsuyama:
            print()
            print("CHECK: Matsuyama (75) found")
        else:
            print()
            print("WARNING: Matsuyama (75) not found")
            all_ok = False

    print()
    print("=" * 64)
    if all_ok:
        print("WINTICKET 3-DAY FUTURE TEST OK")
        sys.exit(0)
    else:
        print("WINTICKET TEST FINISHED WITH MISSING DATA")
        sys.exit(1)


if __name__ == "__main__":
    main()
