import re
import sys
import urllib.request
from html.parser import HTMLParser

DATES = ["20260815", "20260816"]

URL_TEMPLATE = "https://keirin.jp/pc/raceschedule?scym={month}&scyy={year}"

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

VENUES = {
    "函館","青森","いわき平","弥彦","前橋","取手","宇都宮","大宮","西武園","京王閣",
    "立川","松戸","川崎","平塚","小田原","伊東","静岡","名古屋","岐阜","大垣",
    "豊橋","富山","松阪","四日市","福井","奈良","向日町","和歌山","岸和田",
    "玉野","広島","防府","高松","小松島","高知","松山","小倉","久留米","武雄",
    "佐世保","別府","熊本"
}

GRADE_BY_SRC = {
    "ico_f1.png": "FI",
    "ico_f2.png": "FII",
    "ico_g1.png": "GI",
    "ico_g2.png": "GII",
    "ico_g3.png": "GIII",
}

TYPE_BY_SRC = {
    "ico_kaisai_3.png": ("ナイター", "🌙"),
    "ico_kaisai_5.png": ("ミッドナイト", "⭐"),
    "ico_kaisai_8.png": ("モーニング", "🌅"),
}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as res:
        raw = res.read()
        print("HTTP", res.status, url)

    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="ignore")


class ScheduleParser(HTMLParser):
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

        elif tag == "td" and self.in_tr:
            self.in_td = True
            try:
                colspan = int(attrs.get("colspan", "1") or "1")
            except Exception:
                colspan = 1

            self.cell = {
                "text": [],
                "imgs": [],
                "colspan": max(1, colspan),
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
        if tag == "td" and self.in_td:
            self.in_td = False
            self.row.append(self.cell)
            self.cell = None

        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            if self.row:
                self.rows.append(self.row)
            self.row = []


def normalize_venue(cell):
    text = re.sub(r"\s+", "", " ".join(cell.get("text", [])))
    for venue in VENUES:
        if venue in text:
            return venue
    return ""


def classify_cell(cell):
    grade = ""
    day_type = "デイ"
    emoji = "☀️"

    combined_text = " ".join(
        cell.get("text", [])
        + [x.get("alt", "") for x in cell.get("imgs", [])]
        + [x.get("title", "") for x in cell.get("imgs", [])]
    )

    if "ミッドナイト" in combined_text:
        day_type, emoji = "ミッドナイト", "⭐"
    elif "モーニング" in combined_text:
        day_type, emoji = "モーニング", "🌅"
    elif "ナイター" in combined_text:
        day_type, emoji = "ナイター", "🌙"

    icons = []
    for img in cell.get("imgs", []):
        base = img.get("src", "").rsplit("/", 1)[-1]
        icons.append(base)

        if base in GRADE_BY_SRC:
            grade = GRADE_BY_SRC[base]

        if base in TYPE_BY_SRC:
            day_type, emoji = TYPE_BY_SRC[base]

    return {
        "has_event": bool(grade),
        "grade": grade,
        "day_type": day_type,
        "emoji": emoji,
        "icons": icons,
    }


def event_day_label(index_in_span, span):
    if span <= 1:
        return ""
    if index_in_span == 0:
        return "初日"
    if index_in_span == span - 1:
        return "最終日"
    return f"{index_in_span + 1}日目"


def parse_month(year, month):
    source = fetch(
        URL_TEMPLATE.format(year=year, month=f"{month:02d}")
    )

    parser = ScheduleParser()
    parser.feed(source)

    result = {}

    for row in parser.rows:
        if len(row) < 2:
            continue

        venue = normalize_venue(row[0])
        if not venue:
            continue

        # IMPORTANT:
        # KEIRIN.JP uses colspan for one meeting spanning multiple calendar days.
        # Expand each physical <td> into its logical day columns.
        logical_day = 1

        for cell in row[1:]:
            span = max(1, int(cell.get("colspan", 1)))
            info = classify_cell(cell)

            for offset in range(span):
                day = logical_day + offset
                if day > 31:
                    break

                if info["has_event"]:
                    date_str = f"{year:04d}{month:02d}{day:02d}"
                    result.setdefault(date_str, {})[venue] = {
                        **info,
                        "event_day": event_day_label(offset, span),
                        "span": span,
                    }

            logical_day += span

            if logical_day > 31:
                break

    return result


def main():
    data = parse_month(2026, 8)
    ok = True

    for date_str in DATES:
        print()
        print("=" * 70)
        print("KEIRIN.JP FUTURE SCHEDULE:", date_str)
        print("=" * 70)

        venues = data.get(date_str, {})
        print("VENUES:", len(venues))

        for venue, info in venues.items():
            print(
                f"{venue}: "
                f"{info['grade']} "
                f"{info['emoji']}{info['day_type']} "
                f"{info['event_day']} "
                f"span={info['span']} "
                f"icons={','.join(info['icons'])}"
            )

        if "松山" not in venues:
            print("WARNING: 松山 not found")
            ok = False

    print()
    if ok:
        print("KEIRIN.JP FUTURE SCHEDULE COLSPAN TEST OK")
        sys.exit(0)

    print("KEIRIN.JP FUTURE SCHEDULE COLSPAN TEST FAILED")
    sys.exit(1)


if __name__ == "__main__":
    main()
