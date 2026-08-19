from pathlib import Path
import datetime
import html
import re
import urllib.request
import xml.etree.ElementTree as ET

EPG = Path("epg.xml")
JST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(JST).date()
DATE_STR = TODAY.strftime("%Y%m%d")
ISO_DATE = TODAY.strftime("%Y-%m-%d")
DISPLAY_DATE = TODAY.strftime("%Y年%m月%d日")

AUTO = {
    "川口": ("auto.kawaguchi", "kawaguchi"),
    "伊勢崎": ("auto.isesaki", "isesaki"),
    "浜松": ("auto.hamamatsu", "hamamatsu"),
    "飯塚": ("auto.iizuka", "iizuka"),
    "山陽": ("auto.sanyo", "sanyo"),
}

TODAY_URLS = [
    "https://autorace.jp/",
    "https://autorace.jp/race_info/Live/",
]
PROGRAM_URL = "https://autorace.jp/race_info/Program/{slug}/{date}_{race_no}"

UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1"
)


def fetch(url, label):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept-Language": "ja-JP,ja;q=0.9",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read()
        for enc in ("utf-8", "cp932", "shift_jis"):
            try:
                return raw.decode(enc)
            except Exception:
                pass
        return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"{label}: fetch failed: {e}")
        return ""


def plain_text(source):
    source = re.sub(r"(?is)<script.*?</script>", " ", source or "")
    source = re.sub(r"(?is)<style.*?</style>", " ", source)
    source = re.sub(r"(?s)<[^>]+>", " ", source)
    source = html.unescape(source)
    return re.sub(r"\s+", " ", source).strip()


def detect_today_venues():
    pages = []
    for url in TODAY_URLS:
        s = fetch(url, f"AUTORACE TODAY {url}")
        if s:
            pages.append(plain_text(s))

    joined = " ".join(pages)
    if not joined:
        raise SystemExit("AutoRace.JP today's page could not be fetched")

    date_tokens = {
        TODAY.strftime("%Y/%m/%d"),
        f"{TODAY.year}年{TODAY.month}月{TODAY.day}日",
        f"{TODAY.year}/{TODAY.month}/{TODAY.day}",
    }
    if not any(t and t in joined for t in date_tokens):
        print("warning: today's explicit date string not found; continuing with venue-card checks")

    active = {}
    for venue in AUTO:
        matches = list(re.finditer(re.escape(venue) + r"オート", joined))
        best = None
        for m in matches:
            chunk = joined[m.start():m.start() + 700]
            mt = re.search(r"1R\s*([0-2]?\d:[0-5]\d)\s*発走", chunk)
            if not mt:
                continue
            title_chunk = chunk[: mt.start()]
            day_type = "デイ"
            if "オーバーミッドナイト" in title_chunk:
                day_type = "オーバーミッドナイト"
            elif "ミッドナイト" in title_chunk:
                day_type = "ミッドナイト"
            elif "ナイター" in title_chunk:
                day_type = "ナイター"
            elif "モーニング" in title_chunk:
                day_type = "モーニング"
            best = {
                "first": mt.group(1).zfill(5),
                "day_type": day_type,
            }
            break
        if best:
            active[venue] = best

    if not active:
        print("AUTORACE official today: no home-track venues; treating all 5 venues as non-event")
        return {}

    print("AUTORACE official today:", ", ".join(
        f"{v} 1R {i['first']} {i['day_type']}" for v, i in active.items()
    ))
    return active


def parse_program(source, race_no):
    if not source:
        return None
    p = plain_text(source)
    if "該当レースの開催は中止となりました" in p:
        return None

    m = re.search(r"(?:発走予定|発走時刻|発走)\s*[:：]?\s*([0-2]?\d:[0-5]\d)", p)
    time_text = m.group(1) if m else ""
    if not time_text:
        m = re.search(r"投票締切\s*[:：]?\s*([0-2]?\d:[0-5]\d)", p)
        if m:
            hh, mm = map(int, m.group(1).split(":"))
            t = datetime.datetime(2000, 1, 1, hh, mm) + datetime.timedelta(minutes=1)
            time_text = t.strftime("%H:%M")
    if not time_text:
        return None

    name = ""
    m = re.search(rf"([^\s　]{{1,40}}?)\s*{race_no}R\b", p)
    if m:
        name = re.sub(r"\s+", " ", m.group(1)).strip()
    if not name:
        name = "オートレース"

    return {
        "race": race_no,
        "time": time_text.zfill(5),
        "name": name,
        "is_semi": "準決" in name,
        "is_final": "優勝" in name or "決勝" in name,
    }


def get_races(venue, slug, first_hint):
    races = []
    for n in range(1, 13):
        url = PROGRAM_URL.format(slug=slug, date=ISO_DATE, race_no=n)
        r = parse_program(fetch(url, f"AUTORACE {venue} {n}R"), n)
        if r:
            races.append(r)
    if not races:
        races.append({"race": 1, "time": first_hint, "name": "開催予定", "provisional": True})
    return races


def day_emoji(day_type):
    return {
        "モーニング": "🌅",
        "デイ": "☀️",
        "ナイター": "🌙",
        "ミッドナイト": "⭐",
        "オーバーミッドナイト": "🌌",
    }.get(day_type, "☀️")


def maybe_over_midnight(races, fallback):
    valid = []
    for r in races:
        try:
            hh, mm = map(int, r["time"].split(":"))
            valid.append(hh * 60 + mm)
        except Exception:
            pass
    if valid and valid[-1] + 30 > 23 * 60 + 40:
        return "オーバーミッドナイト"
    return fallback


def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S +0900")


def add_prog(root, cid, start, stop, title, desc):
    if stop <= start:
        return
    p = ET.Element("programme", start=fmt(start), stop=fmt(stop), channel=cid)
    ET.SubElement(p, "title", lang="ja").text = title
    ET.SubElement(p, "desc", lang="ja").text = desc
    root.append(p)


def main():
    active = detect_today_venues()
    tree = ET.parse(EPG)
    root = tree.getroot()

    day_start = datetime.datetime.combine(TODAY, datetime.time(8, 0), tzinfo=JST)
    day_end = datetime.datetime.combine(TODAY, datetime.time(23, 59), tzinfo=JST)

    auto_ids = {cid for cid, _ in AUTO.values()}
    for prog in list(root.findall("programme")):
        if prog.get("channel") not in auto_ids:
            continue
        m = re.match(r"(\d{14})", prog.get("start", ""))
        if not m:
            continue
        dt = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(tzinfo=JST)
        if dt.date() == TODAY and dt >= day_start:
            root.remove(prog)

    for venue, (cid, slug) in AUTO.items():
        info = active.get(venue)
        if not info:
            add_prog(
                root, cid, day_start, day_end,
                f"🌼🏍️ 本日は開催していません 💤🍀 {venue}（オートレース）",
                f"AutoRace.JP公式『本日の開催』に{DISPLAY_DATE}の{venue}本場開催は掲載されていません。",
            )
            continue

        races = get_races(venue, slug, info["first"])
        day_type = maybe_over_midnight(races, info["day_type"])
        emoji = day_emoji(day_type)

        race_dts = []
        for r in races:
            hh, mm = map(int, r["time"].split(":"))
            dt = datetime.datetime.combine(TODAY, datetime.time(hh, mm), tzinfo=JST)
            race_dts.append((r, dt))

        first_r, first_dt = race_dts[0]
        pre_stop = max(day_start, first_dt - datetime.timedelta(minutes=10))
        if day_start < pre_stop:
            add_prog(
                root, cid, day_start, pre_stop,
                f"🏍️ {venue}　本日開催　第1️⃣R {first_r['time']}発走予定❗️ {emoji}{day_type}",
                f"AutoRace.JP公式で本日開催を確認。\n1R発走予定 {first_r['time']}\n開催区分: {day_type}\n📅 {DISPLAY_DATE}",
            )

        if first_r.get("provisional"):
            add_prog(
                root, cid, pre_stop, day_end,
                f"📅 開催予定 {venue} {emoji}{day_type} 1R {first_r['time']}発走",
                "本日の開催は公式で確認済みです。各R詳細は一時的に取得できていません。",
            )
            continue

        for i, (r, dt) in enumerate(race_dts):
            start = max(day_start, dt - datetime.timedelta(minutes=10))
            if i + 1 < len(race_dts):
                stop = race_dts[i + 1][1] - datetime.timedelta(minutes=10)
            else:
                stop = dt + datetime.timedelta(minutes=30)
            if stop <= start:
                stop = dt + datetime.timedelta(minutes=12)

            deco = ""
            if r.get("is_final"):
                deco = "🏆決勝🏆 "
            elif r.get("is_semi"):
                deco = "🔥準決勝🔥 "

            add_prog(
                root, cid, start, min(stop, day_end),
                f"{deco}🏍️ {venue} {r['race']}R {r['time']}発走 {r['name']}",
                f"🏍️ オートレース {venue}\n{emoji} 開催区分: {day_type}\n⏰ 発走予定: {r['time']}\n📢 {r['name']}\n📅 {DISPLAY_DATE}",
            )

        finish = race_dts[-1][1] + datetime.timedelta(minutes=30)
        if finish < day_end:
            add_prog(
                root, cid, finish, day_end,
                f"🏁✨ 本日の開催は終了しました 🏍️🌙 {venue}（オートレース）",
                f"{venue}の本日のオートレースは全て終了しました。",
            )

    channels = [x for x in list(root) if x.tag == "channel"]
    programmes = [x for x in list(root) if x.tag == "programme"]
    programmes.sort(key=lambda x: (x.get("start", ""), x.get("channel", "")))
    for x in list(root):
        root.remove(x)
    for x in channels + programmes:
        root.append(x)

    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ")
    tree.write(EPG, encoding="utf-8", xml_declaration=True)
    print("AutoRace today official fix complete")


if __name__ == "__main__":
    main()
