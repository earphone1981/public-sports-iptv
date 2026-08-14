import html
import re
import sys
import urllib.error
import urllib.request
import http.cookiejar

TARGET_DATE = "20260815"
URL = "https://www.jra.go.jp/keiba/calendar2026/2026/8/0815.html"

VENUES = ["東京","中山","新潟","福島","京都","阪神","中京","小倉","札幌","函館"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def fetch_bytes(opener, url, referer=None):
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=30) as res:
        body = res.read()
        ctype = res.headers.get("Content-Type", "")
        print("HTTP:", res.status, res.geturl())
        print("Content-Type:", ctype)
        print("Bytes:", len(body))
        return body, ctype


def decode_best(body, ctype):
    candidates = []

    m = re.search(r"charset=([A-Za-z0-9_\-]+)", ctype or "", re.I)
    if m:
        candidates.append(m.group(1))

    head = body[:5000].decode("ascii", errors="ignore")
    m = re.search(r'charset=["\']?\s*([A-Za-z0-9_\-]+)', head, re.I)
    if m:
        candidates.append(m.group(1))

    candidates += ["utf-8", "cp932", "shift_jis", "euc_jp"]

    seen = set()
    for enc in candidates:
        enc = enc.lower()
        if enc in seen:
            continue
        seen.add(enc)
        try:
            text = body.decode(enc)
        except Exception:
            continue

        score = sum(text.count(v) for v in VENUES)
        score += text.count("レース") + text.count("発走時刻")
        print(f"Decode candidate {enc}: score={score}")
        if score > 5:
            print("Selected encoding:", enc)
            return text

    print("Could not confidently detect encoding; using utf-8 replacement.")
    return body.decode("utf-8", errors="replace")


def strip_html_tags(source):
    source = re.sub(r"(?is)<script.*?</script>", " ", source)
    source = re.sub(r"(?is)<style.*?</style>", " ", source)
    source = re.sub(r"(?s)<[^>]+>", " ", source)
    source = html.unescape(source)
    return re.sub(r"\s+", " ", source).strip()


def main():
    print("JRA DEBUG:", TARGET_DATE)

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)
    )

    try:
        try:
            fetch_bytes(opener, "https://www.jra.go.jp/", "https://www.google.com/")
            print("JRA top page: OK")
        except Exception as e:
            print("JRA top page failed:", repr(e))

        body, ctype = fetch_bytes(
            opener,
            URL,
            "https://www.jra.go.jp/keiba/calendar/"
        )
    except urllib.error.HTTPError as e:
        print("FAILED HTTP:", e.code, e.reason)
        sys.exit(2)

    source = decode_best(body, ctype)
    plain = strip_html_tags(source)

    print()
    print("===== BASIC CHECK =====")
    for word in ["2026年8月15日", "新潟", "中京", "札幌", "レース", "発走時刻"]:
        print(f"{word}: {plain.count(word)}")

    print()
    print("===== VENUE CONTEXT =====")
    for venue in ["新潟", "中京", "札幌"]:
        pos = plain.find(venue)
        print(f"--- {venue} pos={pos} ---")
        if pos >= 0:
            print(plain[max(0, pos-180):pos+900])
        else:
            print("NOT FOUND")

    print()
    print("===== RACE SAMPLE =====")
    for pat in [
        r"1\s*レース.{0,250}",
        r"1R.{0,250}",
        r"9\s*時\s*40\s*分.{0,100}",
    ]:
        m = re.search(pat, plain, flags=re.S)
        print("PATTERN:", pat)
        print(m.group(0) if m else "NO MATCH")

    print()
    print("===== HEADING TEST =====")
    heading_re = re.compile(
        r"(\d+)\s*回\s*(東京|中山|新潟|福島|京都|阪神|中京|小倉|札幌|函館)\s*(\d+)\s*日"
    )
    matches = list(heading_re.finditer(plain))
    print("Heading matches:", len(matches))
    for m in matches[:10]:
        print(m.group(0), "venue=", m.group(2), "pos=", m.start())

    print()
    print("JRA DEBUG END")


if __name__ == "__main__":
    main()
