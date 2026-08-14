import re
import sys
import urllib.request
from html.parser import HTMLParser

DATES = ["20260815", "20260816"]

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

VENUES = ["川口", "伊勢崎", "浜松", "飯塚", "山陽"]

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


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_tr = False
        self.in_td = False
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.in_tr = True
            self.row = []
        elif tag in ("td", "th") and self.in_tr:
            self.in_td = True
            try:
                colspan = int(attrs.get("colspan", "1") or "1")
            except Exception:
                colspan = 1
            self.cell = {
                "text": [],
                "imgs": [],
                "colspan": max(1, colspan),
                "tag": tag,
            }
        elif tag == "img" and self.in_td and self.cell is not None:
            self.cell["imgs"].append({
                "src": attrs.get("src", ""),
                "alt": attrs.get("alt", ""),
                "title": attrs.get("title", ""),
            })

    def handle_data(self, data):
        if self.in_td and self.cell is not None:
            t = re.sub(r"\s+", " ", data).strip()
            if t:
                self.cell["text"].append(t)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.in_td:
            self.in_td = False
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            if self.row:
                self.rows.append(self.row)
            self.row = []


def cell_text(cell):
    return " ".join(cell.get("text", []))


def classify(cell):
    txt = " ".join(
        [cell_text(cell)]
        + [x.get("alt", "") for x in cell.get("imgs", [])]
        + [x.get("title", "") for x in cell.get("imgs", [])]
    )

    grade = "普通開催"
    for g in ("SG", "G1", "G2"):
        if re.search(rf"(?<![A-Z0-9]){g}(?![A-Z0-9])", txt, re.I):
            grade = g
            break

    if "オーバーミッドナイト" in txt:
        pattern, emoji = "オーバーミッドナイト", "🌑"
    elif "ミッドナイト" in txt:
        pattern, emoji = "ミッドナイト", "⭐"
    elif "モーニング" in txt:
        pattern, emoji = "モーニング", "🌅"
    elif "ナイター" in txt:
        pattern, emoji = "ナイター", "🌙"
    else:
        pattern, emoji = "デイ", "☀️"

    return grade, pattern, emoji


def detect_date_from_header(cell, year="2026", month="08"):
    txt = cell_text(cell)
    m = re.search(r"(\d{1,2})\s*[/月]\s*(\d{1,2})", txt)
    if m:
        mm = int(m.group(1))
        dd = int(m.group(2))
        return f"{year}{mm:02d}{dd:02d}"
    m = re.search(r"\b(\d{1,2})日\b", txt)
    if m:
        dd = int(m.group(1))
        return f"{year}{int(month):02d}{dd:02d}"
    return ""


def parse_calendar(source):
    p = TableParser()
    p.feed(source)

    # Build a date-column map from header-looking rows.
    date_cols = {}
    for row in p.rows:
        logical = 0
        found_any = False
        temp = {}
        for cell in row:
            span = max(1, cell.get("colspan", 1))
            ds = detect_date_from_header(cell)
            if ds:
                for off in range(span):
                    temp[logical + off] = ds
                found_any = True
            logical += span
        if found_any and len(temp) >= 2:
            date_cols = temp
            break

    result = {}

    for row in p.rows:
        # Find venue cell.
        venue = ""
        venue_idx = None
        logical_idx = 0
        for i, cell in enumerate(row):
            txt = cell_text(cell)
            matched = next((v for v in VENUES if v in txt), None)
            if matched:
                venue = matched
                venue_idx = i
                break
            logical_idx += max(1, cell.get("colspan", 1))

        if not venue or venue_idx is None:
            continue

        # Expand cells after the venue cell across logical columns.
        logical = 0
        for i, cell in enumerate(row):
            span = max(1, cell.get("colspan", 1))
            if i <= venue_idx:
                logical += span
                continue

            grade, pattern, emoji = classify(cell)

            # Empty non-event cells are ignored.
            raw = cell_text(cell) + " " + " ".join(x.get("alt", "") for x in cell.get("imgs", []))
            if not raw.strip():
                logical += span
                continue

            for off in range(span):
                col = logical + off
                ds = date_cols.get(col)
                if ds in DATES:
                    result.setdefault(ds, {})[venue] = {
                        "grade": grade,
                        "pattern": pattern,
                        "emoji": emoji,
                        "raw": raw.strip()[:200],
                    }

            logical += span

    return result


def main():
    merged = {d: {} for d in DATES}

    for url in URLS:
        try:
            src = fetch(url)
        except Exception as e:
            print("FETCH FAILED", url, repr(e))
            continue

        parsed = parse_calendar(src)
        for ds, venues in parsed.items():
            for venue, info in venues.items():
                merged.setdefault(ds, {})[venue] = info

    print()
    print("=" * 72)
    print("AUTORACE CELL-BASED FUTURE SCHEDULE TEST")
    print("=" * 72)

    for ds in DATES:
        print()
        print("DATE:", ds)
        venues = merged.get(ds, {})
        if not venues:
            print("  NONE")
            continue
        for venue, info in venues.items():
            print(
                f"  {venue}: [{info['grade']}] "
                f"{info['emoji']}{info['pattern']} "
                f"raw={info['raw']}"
            )

    print()
    print("TEST FINISHED")
    sys.exit(0)

if __name__ == "__main__":
    main()
