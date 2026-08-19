from pathlib import Path
import datetime
import re
import xml.etree.ElementTree as ET

EPG = Path("epg.xml")
M3U = Path("public_sports.m3u")
JST = datetime.timezone(datetime.timedelta(hours=9))
TODAY = datetime.datetime.now(JST).date()

SORT_GROUPS = {"競輪", "地方競馬", "オートレース", "ボートレース"}
ORDER = {
    "モーニング": 0,
    "デイ": 1,
    "通常": 1,
    "薄暮": 2,
    "サマータイム": 2,
    "ナイター": 3,
    "ミッドナイト": 4,
    "オーバーミッドナイト": 5,
}

RACE_TIME_RE = re.compile(r"([0-2]?\d:[0-5]\d)\s*発走")
TVG_ID_RE = re.compile(r'tvg-id="([^"]+)"', re.I)


def parse_dt(value):
    m = re.match(r"(\d{14})\s*([+-]\d{4})?", str(value or ""))
    if not m:
        return None
    digits, off = m.groups()
    if off:
        return datetime.datetime.strptime(f"{digits} {off}", "%Y%m%d%H%M%S %z").astimezone(JST)
    return datetime.datetime.strptime(digits, "%Y%m%d%H%M%S").replace(tzinfo=JST)


def classify_from_desc(desc, first_minutes, last_minutes):
    for key in ("オーバーミッドナイト", "ミッドナイト", "ナイター", "サマータイム", "薄暮", "モーニング", "デイ", "通常"):
        if key in desc:
            return key
    if last_minutes is not None and last_minutes + 30 > 23 * 60 + 40:
        return "オーバーミッドナイト"
    if first_minutes is None:
        return "非開催"
    if first_minutes < 10 * 60:
        return "モーニング"
    if first_minutes >= 19 * 60:
        return "ミッドナイト"
    if first_minutes >= 14 * 60:
        return "ナイター"
    return "デイ"


def build_epg_keys():
    root = ET.parse(EPG).getroot()
    by_channel = {}

    for p in root.findall("programme"):
        cid = p.get("channel", "")
        if not cid:
            continue
        start = parse_dt(p.get("start"))
        if start is None:
            continue
        logical_date = start.date() if start.hour >= 4 else start.date() - datetime.timedelta(days=1)
        if logical_date != TODAY:
            continue

        title = p.findtext("title") or ""
        desc = p.findtext("desc") or ""
        if "本日は開催していません" in title or "データ取得準備中" in title:
            by_channel.setdefault(cid, {"times": [], "desc": "", "non_event": True})
            continue

        m = RACE_TIME_RE.search(title)
        if not m:
            m = re.search(r"発走予定[:：]?\s*([0-2]?\d:[0-5]\d)", desc)
        if not m:
            continue

        hh, mm = map(int, m.group(1).split(":"))
        minutes = hh * 60 + mm
        info = by_channel.setdefault(cid, {"times": [], "desc": "", "non_event": False})
        info["times"].append(minutes)
        info["desc"] += " " + desc
        info["non_event"] = False

    keys = {}
    for cid, info in by_channel.items():
        times = sorted(info["times"])
        if not times:
            keys[cid] = (99, 9999, cid)
            continue
        first = times[0]
        last = times[-1]
        day_type = classify_from_desc(info["desc"], first, last)
        keys[cid] = (ORDER.get(day_type, 50), first, cid)
    return keys


def split_sections(text):
    lines = text.replace("\r\n", "\n").split("\n")
    header = []
    sections = []
    current_name = None
    current_lines = []

    for line in lines:
        if line.startswith("## "):
            if current_name is None:
                if current_lines:
                    header.extend(current_lines)
            else:
                sections.append((current_name, current_lines))
            current_name = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_name is None:
        header.extend(current_lines)
    else:
        sections.append((current_name, current_lines))
    return header, sections


def parse_blocks(lines):
    prefix = [lines[0]] if lines else []
    blocks = []
    i = 1
    while i < len(lines):
        if not lines[i].startswith("#EXTINF:"):
            i += 1
            continue
        block = [lines[i]]
        i += 1
        while i < len(lines) and not lines[i].startswith("#EXTINF:"):
            block.append(lines[i])
            i += 1
        while block and block[-1] == "":
            block.pop()
        blocks.append(block)
    return prefix, blocks


def block_id(block):
    if not block:
        return ""
    m = TVG_ID_RE.search(block[0])
    return m.group(1).strip() if m else ""


def main():
    epg_keys = build_epg_keys()
    text = M3U.read_text(encoding="utf-8-sig")
    header, sections = split_sections(text)
    out = []

    if header:
        out.extend(header)
        while out and out[-1] == "":
            out.pop()
        out.append("")

    for name, lines in sections:
        if name not in SORT_GROUPS:
            out.extend(lines)
            if out and out[-1] != "":
                out.append("")
            continue

        prefix, blocks = parse_blocks(lines)
        decorated = []
        for original_index, block in enumerate(blocks):
            cid = block_id(block)
            key = epg_keys.get(cid, (99, 9999, cid or f"zz{original_index:04d}"))
            decorated.append((key, original_index, block))
        decorated.sort(key=lambda x: (x[0], x[1]))

        out.extend(prefix)
        for _, _, block in decorated:
            out.extend(block)
            out.append("")

        print(f"{name}: {len(blocks)} ch sorted")

    result = "\n".join(out).rstrip() + "\n"
    M3U.write_text(result, encoding="utf-8")
    print("public_sports.m3u sorted from today's EPG")


if __name__ == "__main__":
    main()
