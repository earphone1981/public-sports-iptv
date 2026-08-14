import re
import sys
import urllib.request
from html.parser import HTMLParser

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

KEYWORDS = [
    "2026",
    "8月15日",
    "8月16日",
    "08/15",
    "08/16",
    "15日",
    "16日",
    "川口",
    "伊勢崎",
    "浜松",
    "飯塚",
    "山陽",
    "SG",
    "G1",
    "G2",
    "モーニング",
    "ナイター",
    "ミッドナイト",
    "オーバーミッドナイト",
]


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        ctype = r.headers.get("Content-Type", "")
        print("HTTP", r.status, url)
        print("Content-Type:", ctype)
        print("Bytes:", len(raw))

    # choose decode with best Japanese keyword score
    best = ""
    best_score = -1
    for enc in ("utf-8", "cp932", "shift_jis", "euc_jp"):
        try:
            txt = raw.decode(enc)
        except Exception:
            continue
        score = sum(txt.count(k) for k in KEYWORDS)
        if score > best_score:
            best = txt
            best_score = score

    print("Decode score:", best_score)
    return best or raw.decode("utf-8", errors="ignore")


class DumpParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.stack.append((tag, attrs))

        if tag in ("table", "tr", "td", "th", "div", "li", "a"):
            cls = attrs.get("class", "")
            ident = attrs.get("id", "")
            href = attrs.get("href", "")
            if cls or ident or href:
                self.items.append(
                    f"START <{tag}> class={cls!r} id={ident!r} href={href!r}"
                )

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()

    def handle_data(self, data):
        t = re.sub(r"\s+", " ", data).strip()
        if not t:
            return
        if any(k in t for k in KEYWORDS):
            path = " > ".join(x[0] for x in self.stack[-6:])
            self.items.append(f"TEXT [{path}] {t[:500]}")


def main():
    for url in URLS:
        print()
        print("=" * 90)
        print("URL:", url)
        print("=" * 90)

        try:
            src = fetch(url)
        except Exception as e:
            print("FETCH FAILED:", repr(e))
            continue

        print()
        print("===== RAW KEYWORD CONTEXT =====")
        for kw in ["8月15日", "8月16日", "08/15", "08/16", "15日", "16日", "伊勢崎", "飯塚"]:
            print()
            print("---", kw, "---")
            matches = list(re.finditer(re.escape(kw), src))
            print("count=", len(matches))
            for m in matches[:5]:
                a = max(0, m.start() - 500)
                b = min(len(src), m.end() + 1200)
                snippet = re.sub(r"\s+", " ", src[a:b])
                print(snippet[:1700])

        print()
        print("===== STRUCTURE ITEMS =====")
        p = DumpParser()
        p.feed(src)
        for item in p.items[:500]:
            print(item)

    print()
    print("AUTORACE CALENDAR DEBUG END")
    sys.exit(0)


if __name__ == "__main__":
    main()
