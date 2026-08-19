from pathlib import Path
import datetime
import re
import xml.etree.ElementTree as ET

JST = datetime.timezone(datetime.timedelta(hours=9))
LIVE_PREFIX = "🔴📺 ただいま実況放送中！！！ 📺🔴"
FINISHED_TITLE = "⛔🏁 本日の全レースは終了しました 🏁⛔"
NON_EVENT_TITLE = "🚫💤 本日は開催していません 💤🚫"
TARGET_PREFIXES = ("keirin.", "chihou.", "keiba.", "auto.", "boat.")
TARGET_JRA = {"jra.east", "jra.west", "jra.hokkaido"}

SPECIAL_KEIRIN = {
    "keirin.kawasaki": "かわさき",
    "keirin.nagoya": "なごや",
    "keirin.kochi": "こうち",
}
SPECIAL_KEIRIN_FULL = {
    "keirin.pist6": "千葉PIST6（休止中）",
    "keirin.takamatsu": "高松けいりん（休止中）",
    "keirin.mukomachi": "向日町けいりん（休止中）",
}

R_CIRCLED = {
    1: "❶", 2: "❷", 3: "❸", 4: "❹", 5: "❺", 6: "❻",
    7: "❼", 8: "❽", 9: "❾", 10: "❿", 11: "⓫", 12: "⓬",
}


def parse_xmltv(value):
    s = str(value or "").strip()
    m = re.match(r"(\d{14})\s*([+-]\d{4})?", s)
    if not m:
        return None
    digits, off = m.groups()
    if off:
        return datetime.datetime.strptime(f"{digits} {off}", "%Y%m%d%H%M%S %z").astimezone(JST)
    return datetime.datetime.strptime(digits, "%Y%m%d%H%M%S").replace(tzinfo=JST)


def fmt_xmltv(dt):
    return dt.astimezone(JST).strftime("%Y%m%d%H%M%S +0900")


def is_target(cid):
    return cid.startswith(TARGET_PREFIXES) or cid in TARGET_JRA


def clean_base_name(name):
    s = str(name or "").strip()
    s = re.sub(r"^\d{1,2}\s+", "", s)
    s = s.replace("Ⓚ", "")
    for suffix in ("けいりん", "けいば", "オート"):
        if s.endswith(suffix):
            s = s[:-len(suffix)]
    if s.startswith("BOATRACE"):
        s = s[len("BOATRACE"):]
    return s.strip()


def standardized_name(cid, current):
    if cid in SPECIAL_KEIRIN_FULL:
        return SPECIAL_KEIRIN_FULL[cid]
    base = clean_base_name(current)
    if cid.startswith("keirin."):
        base = SPECIAL_KEIRIN.get(cid, base)
        return f"{base}けいりん"
    if cid.startswith(("chihou.", "keiba.")):
        return f"{base}けいば"
    if cid.startswith("auto."):
        return f"{base}オート"
    if cid.startswith("boat."):
        return f"BOATRACE{base}"
    return current


def extract_race_parts(title):
    t = str(title or "").strip()
    # 場名 + 通常R表記 + 発走時刻を元データから拾う。
    m = re.search(
        r"(?P<venue>[^\s【】]+)\s+(?P<race>\d{1,2})R\s+(?P<time>\d{1,2}:\d{2})発走\s*(?P<rest>.*)$",
        t,
    )
    if not m:
        return None
    venue = m.group("venue")
    race_no = m.group("race")
    race_time = m.group("time")
    rest = m.group("rest").strip()

    rest = re.sub(r"^(?:🌅|☀️|🌇|🌙|⭐|🌃|🌌|🚲|🚤|🏍️|🏇|💛)+\s*", "", rest)
    rest = re.sub(r"^(?:モーニング|通常|デイ|薄暮|サマータイム|ナイター|ミッドナイト|オーバーミッドナイト)\s*", "", rest)

    brackets = re.findall(r"【([^】]+)】", rest)
    plain = re.sub(r"\s*【[^】]+】\s*", " ", rest)
    plain = re.sub(r"\s+", " ", plain).strip()

    detail = brackets[-1].strip() if brackets else plain
    if not detail:
        detail = plain or "レース"

    front_name = plain or detail
    front_name = re.sub(r"^(?:🏆\s*MAIN\s*)", "", front_name).strip()
    front_name = re.sub(r"^[🚲🚤🏍️🏇💛]+\s*", "", front_name).strip()

    return venue, race_no, race_time, front_name, detail


def race_no_deco(race_no):
    try:
        n = int(str(race_no).strip())
    except Exception:
        return f"{race_no}ℛ"
    return f"{R_CIRCLED.get(n, str(n))}ℛ"


def competition_icon(cid, detail):
    d = str(detail or "")
    if re.search(r"[LＬ]級|ガールズ", d):
        return "💛"
    if cid.startswith("boat."):
        return "🚤"
    if cid.startswith("auto."):
        return "🏍️"
    if cid.startswith(("chihou.", "keiba.")) or cid in TARGET_JRA:
        return "🏇"
    if cid.startswith("keirin."):
        return "🚲"
    return ""


def front_deco(detail):
    d = re.sub(r"\s+", " ", str(detail or "")).strip()
    if re.search(r"優勝|決勝|ファイナル", d):
        return "🏆決勝🏆"
    if "準決" in d:
        return "🔥準決勝🔥"
    if re.search(r"G[ⅠI1]|ＧⅠ|JpnI\b", d, re.I):
        return "👑GⅠ👑"
    if re.search(r"G[ⅡI2]|ＧⅡ|JpnII\b", d, re.I):
        return "✨GⅡ✨"
    if re.search(r"G[ⅢI3]|ＧⅢ|JpnIII\b", d, re.I):
        return "🌟GⅢ🌟"
    return ""


def decorate_detail(detail, cid):
    d = re.sub(r"\s+", " ", str(detail or "レース")).strip()
    if re.search(r"[LＬ]級|ガールズ", d):
        return f"💛【{d} 💛】"
    if re.search(r"優勝|決勝|ファイナル", d):
        return f"🏆【{d}】🏆"
    if "準決" in d:
        return f"🔥【{d}】🔥"
    if re.search(r"G[ⅠI1]|ＧⅠ|JpnI\b", d, re.I):
        return f"👑【{d}】👑"
    if re.search(r"G[ⅡI2]|ＧⅡ|JpnII\b", d, re.I):
        return f"✨【{d}】✨"
    if re.search(r"G[ⅢI3]|ＧⅢ|JpnIII\b", d, re.I):
        return f"🌟【{d}】🌟"
    icon = competition_icon(cid, d)
    return f"{icon}【{d} {icon}】" if icon else f"【{d}】"


def build_live_title(race_no, detail, cid):
    # 朝に決めた仕様：レース番号を必ず前面へ。準決・決勝・G級も前面で強調。
    parts = []
    deco = front_deco(detail)
    if deco:
        parts.append(deco)
    icon = competition_icon(cid, detail)
    if icon:
        parts.append(icon)
    parts.append(race_no_deco(race_no))
    parts.append(LIVE_PREFIX)
    return f"{' '.join(parts)}｜{decorate_detail(detail, cid)}"


def resolve_post_time(programme, race_time):
    start = parse_xmltv(programme.get("start"))
    if start is None:
        return None
    h, minute = map(int, race_time.split(":"))
    base = start.date()
    candidates = [
        datetime.datetime.combine(base + datetime.timedelta(days=d), datetime.time(h, minute), tzinfo=JST)
        for d in (-1, 0, 1)
    ]
    return min(candidates, key=lambda x: abs((x - start).total_seconds()))


def main():
    path = Path("epg.xml")
    tree = ET.parse(path)
    root = tree.getroot()

    for ch in root.findall("channel"):
        cid = ch.get("id", "")
        if not is_target(cid):
            continue
        dn = ch.find("display-name")
        current = dn.text if dn is not None and dn.text else ""
        new_name = standardized_name(cid, current)
        if dn is None:
            dn = ET.SubElement(ch, "display-name")
        dn.text = new_name

    by_channel = {}
    formatted = 0

    for p in root.findall("programme"):
        cid = p.get("channel", "")
        if not is_target(cid):
            continue
        title_el = p.find("title")
        if title_el is None:
            continue
        title = title_el.text or ""

        if "本日は開催していません" in title:
            title_el.text = NON_EVENT_TITLE
            continue
        if "本日の開催は終了しました" in title or "本日の全レースは終了しました" in title:
            title_el.text = FINISHED_TITLE
            continue

        parts = extract_race_parts(title)
        if not parts:
            continue

        venue, race_no, race_time, front_name, detail = parts
        post = resolve_post_time(p, race_time)
        if post is None:
            continue

        title_el.text = build_live_title(race_no, detail, cid)
        by_channel.setdefault(cid, []).append((post, p))
        formatted += 1

    # 発走1分後に次レース表示へ切替
    adjusted = 0
    for cid, items in by_channel.items():
        items.sort(key=lambda x: x[0])
        groups = {}
        for post, p in items:
            key = post.date() if post.hour >= 4 else post.date() - datetime.timedelta(days=1)
            groups.setdefault(key, []).append((post, p))

        for races in groups.values():
            races.sort(key=lambda x: x[0])
            previous_cut = None
            for post, p in races:
                own_cut = post + datetime.timedelta(minutes=1)
                old_start = parse_xmltv(p.get("start"))
                new_start = previous_cut if previous_cut is not None else old_start
                if new_start is not None and new_start < own_cut:
                    p.set("start", fmt_xmltv(new_start))
                    p.set("stop", fmt_xmltv(own_cut))
                    adjusted += 1
                previous_cut = own_cut

    # 深夜の準備中は01:00から
    for p in root.findall("programme"):
        cid = p.get("channel", "")
        if not is_target(cid):
            continue
        title = p.findtext("title") or ""
        if "データ取得準備中" not in title:
            continue
        start = parse_xmltv(p.get("start"))
        stop = parse_xmltv(p.get("stop"))
        if start and stop and start.hour == 0 and start.minute == 0:
            new_start = start.replace(hour=1)
            if new_start < stop:
                p.set("start", fmt_xmltv(new_start))

    ET.indent(tree, space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print(f"EPG v11 finalized: titles={formatted} timing={adjusted}")


if __name__ == "__main__":
    main()
