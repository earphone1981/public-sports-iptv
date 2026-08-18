from pathlib import Path
import datetime
import re
import xml.etree.ElementTree as ET

JST = datetime.timezone(datetime.timedelta(hours=9))

LIVE_PREFIX = "🔴📺 ただいま実況放送中！！！ 📺🔴"
FINISHED_TITLE = "⛔🏁 本日の全レースは終了しました 🏁⛔"
NON_EVENT_TITLE = "🚫💤 本日は開催していません 💤🚫"

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


def clean_base(name: str) -> str:
    s = str(name or "").strip()
    s = re.sub(r"^\d{1,2}\s+", "", s)
    s = s.replace("Ⓚ", "")
    for suffix in ("けいりん", "けいば", "オート"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    if s.startswith("BOATRACE"):
        s = s[len("BOATRACE"):]
    return s.strip()


def standardized_name(tvg_id: str, current: str) -> str:
    if tvg_id in SPECIAL_KEIRIN_FULL:
        return SPECIAL_KEIRIN_FULL[tvg_id]

    # 地方競馬は「帯広けいば（ばんえい競馬）」のように
    # 前半をひらがな表記、括弧内の正式名称をそのまま残す。
    # 括弧の後ろに余計な「けいば」は付けない。
    if tvg_id.startswith(("chihou.", "keiba.")):
        s = str(current or "").strip()
        s = re.sub(r"^\d{1,2}\s+", "", s)
        s = re.sub(r"けいば（([^）]+)）けいば$", r"けいば（\1）", s)
        if re.search(r"けいば（[^）]+）$", s):
            return s
        base = clean_base(s)
        return f"{base}けいば"

    base = clean_base(current)
    if tvg_id.startswith("keirin."):
        base = SPECIAL_KEIRIN.get(tvg_id, base)
        return f"{base}けいりん"
    if tvg_id.startswith("auto."):
        return f"{base}オート"
    if tvg_id.startswith("boat."):
        return f"BOATRACE{base}"
    return current


def is_core_m3u_entry(line: str, tvg_id: str) -> bool:
    if 'group-title="競輪(TIPSTAR)"' in line:
        return tvg_id.startswith("keirin.")
    if 'group-title="地方競馬"' in line or 'group-title="競馬 / 地方競馬"' in line:
        return tvg_id.startswith(("chihou.", "keiba."))
    if 'group-title="オートレース"' in line:
        return tvg_id.startswith("auto.")
    if 'group-title="ボートレース"' in line:
        return tvg_id.startswith("boat.")
    return False


def normalize_m3u(path: Path) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").split("\n")
    out = []
    changed = 0
    for line in lines:
        if not line.startswith("#EXTINF:"):
            out.append(line)
            continue
        m = re.search(r'tvg-id="([^"]+)"', line)
        if not m:
            out.append(line)
            continue
        tvg_id = m.group(1)
        if not is_core_m3u_entry(line, tvg_id):
            out.append(line)
            continue
        n = re.search(r'tvg-name="([^"]*)"', line)
        current = n.group(1) if n else ""
        new_name = standardized_name(tvg_id, current)
        if n:
            line = re.sub(r'tvg-name="[^"]*"', f'tvg-name="{new_name}"', line, count=1)
        else:
            line = line.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-name="{new_name}"', 1)
        if "," in line:
            line = line.rsplit(",", 1)[0] + "," + new_name
        changed += 1
        out.append(line)
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"M3U labels normalized: {changed}")


def parse_xmltv(value: str):
    s = str(value or "").strip()
    m = re.match(r"(\d{14})\s*([+-]\d{4})?", s)
    if not m:
        return None
    digits, off = m.groups()
    if off:
        return datetime.datetime.strptime(f"{digits} {off}", "%Y%m%d%H%M%S %z")
    return datetime.datetime.strptime(digits, "%Y%m%d%H%M%S").replace(tzinfo=JST)


def fmt_xmltv(dt: datetime.datetime) -> str:
    return dt.astimezone(JST).strftime("%Y%m%d%H%M%S +0900")


def category_id(cid: str) -> bool:
    return cid.startswith(("keirin.", "chihou.", "keiba.", "auto.", "boat.")) or cid in {
        "jra.east", "jra.west", "jra.hokkaido"
    }


def race_title(title: str) -> bool:
    t = str(title or "")
    return bool(re.search(r"(?:❶|❷|❸|❹|❺|❻|❼|❽|❾|❿|⓫|⓬|\b\d{1,2}\s*R\b|\b\d{1,2}R\b)", t) and "発走" in t)


def race_detail(title: str, cid: str) -> str:
    t = re.sub(rf"^.*?{re.escape(LIVE_PREFIX)}｜?", "", str(title or "")).strip()
    m = re.search(r"発走\s*(.+)$", t)
    detail = m.group(1).strip() if m else t
    bracket = re.findall(r"【([^】]+)】", detail)
    plain = re.sub(r"\s*【[^】]+】\s*", " ", detail)
    plain = re.sub(r"\s+", " ", plain).strip()
    meta = " ".join(x for x in bracket if x and x not in plain).strip()
    combined = " ".join(x for x in (meta, plain) if x).strip()
    if not combined:
        combined = "レース"
    if re.search(r"[LＬ]級|ガールズ", combined):
        return f"💛【{combined}】"
    if re.search(r"優勝|決勝|ファイナル", combined):
        return f"🏆【{combined}】🏆"
    if "準決" in combined:
        return f"🔥【{combined}】🔥"
    if re.search(r"G[ⅠI1]|ＧⅠ|JpnI\b", combined, re.I):
        return f"👑【{combined}】👑"
    if re.search(r"G[ⅡI2]|ＧⅡ|JpnII\b", combined, re.I):
        return f"✨【{combined}】✨"
    if re.search(r"G[ⅢI3]|ＧⅢ|JpnIII\b", combined, re.I):
        return f"🌟【{combined}】🌟"
    if cid.startswith("boat."):
        return f"🚤【{combined}】"
    if cid.startswith("auto."):
        return f"🏍️【{combined}】"
    if cid.startswith(("chihou.", "keiba.")) or cid.startswith("jra."):
        return f"🏇【{combined}】"
    if cid.startswith("keirin."):
        return f"🚲【{combined}】"
    return f"【{combined}】"


def base_race_title(title: str) -> str:
    t = re.sub(rf"^.*?{re.escape(LIVE_PREFIX)}｜?", "", str(title or "")).strip()
    t = re.sub(r"\s*【[^】]+】\s*$", "", t).strip()
    return t


def normalize_epg(path: Path) -> None:
    if not path.exists():
        return
    tree = ET.parse(path)
    root = tree.getroot()
    channel_names = {}
    for ch in root.findall("channel"):
        cid = ch.get("id", "")
        dn = ch.find("display-name")
        current = dn.text if dn is not None and dn.text else ""
        if category_id(cid):
            new_name = standardized_name(cid, current)
            if dn is None:
                dn = ET.SubElement(ch, "display-name")
            dn.text = new_name
            channel_names[cid] = new_name
    normalized_live = normalized_end = normalized_off = shifted_25h = 0
    for p in root.findall("programme"):
        cid = p.get("channel", "")
        if not category_id(cid):
            continue
        title_el = p.find("title")
        if title_el is None:
            title_el = ET.SubElement(p, "title", {"lang": "ja"})
        title = title_el.text or ""
        if "本日は開催していません" in title:
            title_el.text = NON_EVENT_TITLE
            stop = parse_xmltv(p.get("stop"))
            if stop and stop.hour == 23 and stop.minute >= 50:
                next_1 = (stop + datetime.timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0)
                p.set("stop", fmt_xmltv(next_1)); shifted_25h += 1
            normalized_off += 1; continue
        if "本日の開催は終了しました" in title or "本日の全レースは終了しました" in title:
            title_el.text = FINISHED_TITLE
            stop = parse_xmltv(p.get("stop"))
            if stop and stop.hour == 23 and stop.minute >= 50:
                next_1 = (stop + datetime.timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0)
                p.set("stop", fmt_xmltv(next_1)); shifted_25h += 1
            normalized_end += 1; continue
        if race_title(title):
            detail = race_detail(title, cid)
            base = base_race_title(title)
            title_el.text = f"{base} {LIVE_PREFIX}｜{detail}"
            normalized_live += 1
    for p in root.findall("programme"):
        cid = p.get("channel", "")
        if not category_id(cid):
            continue
        title = p.findtext("title") or ""
        if "データ取得準備中" not in title:
            continue
        start = parse_xmltv(p.get("start")); stop = parse_xmltv(p.get("stop"))
        if start and stop and start.hour == 0 and start.minute == 0 and stop > start:
            new_start = start.replace(hour=1)
            if new_start < stop:
                p.set("start", fmt_xmltv(new_start))
    ET.indent(tree, space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print("EPG normalized:", f"live={normalized_live}", f"finished={normalized_end}", f"off={normalized_off}", f"25h={shifted_25h}")


if __name__ == "__main__":
    normalize_epg(Path("epg.xml"))
    normalize_m3u(Path("public_sports.m3u"))
