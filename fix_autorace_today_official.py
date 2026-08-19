from pathlib import Path
import datetime
import html
import re
import urllib.request
import xml.etree.ElementTree as ET

EPG = Path("epg.xml")
JST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(JST).date()
ISO_DATE = TODAY.strftime("%Y-%m-%d")
DISPLAY_DATE = TODAY.strftime("%Y年%m月%d日")

AUTO = {
    "川口": ("auto.kawaguchi", "kawaguchi"),
    "伊勢崎": ("auto.isesaki", "isesaki"),
    "浜松": ("auto.hamamatsu", "hamamatsu"),
    "飯塚": ("auto.iizuka", "iizuka"),
    "山陽": ("auto.sanyo", "sanyou"),
}

# AutoRace.JP の実際のWEB出走表URLは /Program/Web/... 形式。
PROGRAM_URL = "https://autorace.jp/race_info/Program/Web/{slug}/{date}_{race_no}"

UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1"
)

R_CIRCLED = {
    1: "❶", 2: "❷", 3: "❸", 4: "❹", 5: "❺", 6: "❻",
    7: "❼", 8: "❽", 9: "❾", 10: "❿", 11: "⓫", 12: "⓬",
}


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


def parse_program(source, race_no):
    if not source:
        return None

    p = plain_text(source)
    if "該当レースの開催は中止となりました" in p:
        return None

    # 正常な出走表であることを確認。
    if not re.search(rf"第{race_no}レース|\b{race_no}\s*R\b", p):
        return None

    m = re.search(r"発走予定\s*([0-2]?\d)\s*[:：]\s*([0-5]\d)", p)
    if m:
        time_text = f"{int(m.group(1)):02d}:{m.group(2)}"
    else:
        m = re.search(r"発走予定\s*[:：]?\s*([0-2]?\d:[0-5]\d)", p)
        time_text = m.group(1).zfill(5) if m else ""

    if not time_text:
        m = re.search(r"電投締切\s*([0-2]?\d)\s*[:：]\s*([0-5]\d)", p)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2))
            t = datetime.datetime(2000, 1, 1, hh, mm) + datetime.timedelta(minutes=2)
            time_text = t.strftime("%H:%M")

    if not time_text:
        return None

    name = ""
    # ページ先頭は「山陽オート第1レース | 予選 | ...」のような構造。
    m = re.search(rf"(?:オート)?第{race_no}レース\s*[|｜]?\s*([^|｜]{{1,40}})", p)
    if m:
        candidate = re.sub(r"\s+", " ", m.group(1)).strip()
        if not re.fullmatch(r"20\d{2}年.*", candidate):
            name = candidate

    if not name:
        for word in ("優勝戦", "準決勝戦", "準決勝", "特別選抜戦", "選抜戦", "一般戦", "予選"):
            if word in p:
                name = word
                break

    if not name:
        name = "オートレース"

    return {
        "race": race_no,
        "time": time_text,
        "name": name,
        "is_semi": "準決" in name,
        "is_final": "優勝" in name or ("決勝" in name and "準決" not in name),
    }


def get_races(venue, slug):
    races = []
    fetched = 0

    for n in range(1, 13):
        url = PROGRAM_URL.format(slug=slug, date=ISO_DATE, race_no=n)
        source = fetch(url, f"AUTORACE {venue} {n}R")
        if source:
            fetched += 1
        race = parse_program(source, n)
        if race:
            races.append(race)

    races.sort(key=lambda x: x["race"])
    return races, fetched


def day_type_from_races(races):
    if not races:
        return "デイ"

    first_h = int(races[0]["time"].split(":")[0])
    last_h, last_m = map(int, races[-1]["time"].split(":"))
    end_minutes = last_h * 60 + last_m + 30

    if end_minutes > 23 * 60 + 40:
        return "オーバーミッドナイト"
    if first_h >= 19:
        return "ミッドナイト"
    if first_h >= 14:
        return "ナイター"
    if first_h < 10:
        return "モーニング"
    return "デイ"


def day_emoji(day_type):
    return {
        "モーニング": "🌅",
        "デイ": "☀️",
        "ナイター": "🌙",
        "ミッドナイト": "⭐",
        "オーバーミッドナイト": "🌌",
    }.get(day_type, "☀️")


def fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S +0900")


def add_prog(root, cid, start, stop, title, desc):
    if stop <= start:
        return
    p = ET.Element("programme", start=fmt(start), stop=fmt(stop), channel=cid)
    ET.SubElement(p, "title", lang="ja").text = title
    ET.SubElement(p, "desc", lang="ja").text = desc
    root.append(p)


def race_datetime(time_text, previous=None):
    hh, mm = map(int, time_text.split(":"))
    dt = datetime.datetime.combine(TODAY, datetime.time(hh, mm), tzinfo=JST)
    if previous is not None and dt < previous - datetime.timedelta(hours=6):
        dt += datetime.timedelta(days=1)
    return dt


def main():
    tree = ET.parse(EPG)
    root = tree.getroot()

    day_start = datetime.datetime.combine(TODAY, datetime.time(8, 0), tzinfo=JST)
    end_limit = datetime.datetime.combine(
        TODAY + datetime.timedelta(days=1), datetime.time(1, 0), tzinfo=JST
    )

    replaced = []
    preserved = []

    for venue, (cid, slug) in AUTO.items():
        races, fetched_pages = get_races(venue, slug)

        if not races:
            print(
                f"AUTORACE DIRECT {venue}: races=0 fetched_pages={fetched_pages} "
                "-> existing EPG preserved"
            )
            preserved.append(venue)
            continue

        # 実レースを取得できた場だけ、今日08:00以降を差し替える。
        for prog in list(root.findall("programme")):
            if prog.get("channel") != cid:
                continue
            m = re.match(r"(\d{14})", prog.get("start", ""))
            if not m:
                continue
            dt = datetime.datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(tzinfo=JST)
            if dt.date() == TODAY and dt >= day_start:
                root.remove(prog)

        day_type = day_type_from_races(races)
        emoji = day_emoji(day_type)

        race_dts = []
        prev = None
        for race in races:
            dt = race_datetime(race["time"], prev)
            race_dts.append((race, dt))
            prev = dt

        first_race, first_dt = race_dts[0]
        pre_stop = max(day_start, first_dt - datetime.timedelta(minutes=10))

        if day_start < pre_stop:
            add_prog(
                root,
                cid,
                day_start,
                pre_stop,
                f"⏳ 開催待ち {venue} {emoji}{day_type} 1R {first_race['time']}発走予定",
                f"🏍️ オートレース {venue}\n"
                f"1R発走予定 {first_race['time']}\n"
                f"開催区分: {day_type}\n📅 {DISPLAY_DATE}",
            )

        for i, (race, dt) in enumerate(race_dts):
            start = max(day_start, dt - datetime.timedelta(minutes=10))
            if i + 1 < len(race_dts):
                stop = race_dts[i + 1][1] - datetime.timedelta(minutes=10)
            else:
                stop = dt + datetime.timedelta(minutes=30)

            if stop <= start:
                stop = dt + datetime.timedelta(minutes=12)

            deco = ""
            if race.get("is_final"):
                deco = "🏆決勝🏆 "
            elif race.get("is_semi"):
                deco = "🔥準決勝🔥 "

            add_prog(
                root,
                cid,
                start,
                stop,
                f"{deco}🏍️ {venue} {race['race']}R {race['time']}発走 {race['name']}",
                f"🏍️ オートレース {venue}\n"
                f"{emoji} 開催区分: {day_type}\n"
                f"⏰ 発走予定: {race['time']}\n"
                f"📢 {race['name']}\n📅 {DISPLAY_DATE}",
            )

        finish = race_dts[-1][1] + datetime.timedelta(minutes=30)
        if finish < end_limit:
            add_prog(
                root,
                cid,
                finish,
                end_limit,
                f"🏁✨ 本日の開催は終了しました 🏍️🌙 {venue}（オートレース）",
                f"{venue}の本日のオートレースは全て終了しました。",
            )

        replaced.append(venue)
        print(f"AUTORACE DIRECT {venue}: {len(races)}R / {day_type}")

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

    print("AutoRace direct today fix complete")
    print("replaced:", ", ".join(replaced) if replaced else "none")
    print("preserved:", ", ".join(preserved) if preserved else "none")


if __name__ == "__main__":
    main()
