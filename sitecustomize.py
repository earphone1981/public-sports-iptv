import atexit
import datetime
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

JST = datetime.timezone(datetime.timedelta(hours=9))
TARGET_PREFIXES = ("keirin.", "chihou.", "auto.", "boat.")
TARGET_EXACT = {"jra.east", "jra.west", "jra.hokkaido"}
EXCLUDED = {"jra.gch"}
RACE_TIME_PATTERNS = [
    re.compile(r"(?<!\d)([0-2]?\d):([0-5]\d)\s*発走"),
    re.compile(r"発走(?:予定)?\s*[:：]?\s*([0-2]?\d):([0-5]\d)"),
]
FINISHED_WORDS = ("本日の開催は終了", "本日の競馬は全て終了", "本日の競輪は全て終了", "本日のオートレースは全て終了", "本日のボートレースは全て終了")


def _parse(value):
    s = str(value or "").strip()
    m = re.match(r"^(\d{8,14})\s*([+-]\d{4})?", s)
    if not m:
        return None
    d, off = m.groups()
    d = d + "0" * (14 - len(d))
    try:
        return datetime.datetime.strptime(f"{d} {off}", "%Y%m%d%H%M%S %z") if off else datetime.datetime.strptime(d, "%Y%m%d%H%M%S").replace(tzinfo=JST)
    except Exception:
        return None


def _fmt(dt):
    return dt.strftime("%Y%m%d%H%M%S %z")


def _txt(p, tag):
    n = p.find(tag)
    return (n.text or "") if n is not None else ""


def _target(ch):
    return bool(ch and ch not in EXCLUDED and (ch in TARGET_EXACT or ch.startswith(TARGET_PREFIXES)))


def _race_dt(p):
    text = _txt(p, "title") + " " + _txt(p, "desc")
    hm = None
    for pat in RACE_TIME_PATTERNS:
        m = pat.search(text)
        if m:
            hm = (int(m.group(1)), int(m.group(2)))
            break
    if not hm:
        return None
    start = _parse(p.get("start"))
    if not start:
        return None
    dt = start.astimezone(JST).replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
    sj = start.astimezone(JST)
    if dt < sj - datetime.timedelta(hours=12):
        dt += datetime.timedelta(days=1)
    elif dt > sj + datetime.timedelta(hours=18):
        dt -= datetime.timedelta(days=1)
    return dt


def _apply():
    path = "epg.xml"
    try:
        tree = ET.parse(path)
    except Exception:
        return
    root = tree.getroot()
    grouped = defaultdict(list)
    for p in root.findall("programme"):
        ch = p.get("channel", "")
        if not _target(ch):
            continue
        st = _parse(p.get("start"))
        if st:
            grouped[(ch, st.astimezone(JST).strftime("%Y%m%d"))].append(p)

    changed = 0
    for _, programmes in grouped.items():
        races = [(d, p) for p in programmes if (d := _race_dt(p)) is not None]
        races.sort(key=lambda x: x[0])
        if not races:
            continue
        prev_stop = None
        for i, (rdt, p) in enumerate(races):
            start = _parse(p.get("start")) if i == 0 else prev_stop
            stop = rdt + datetime.timedelta(minutes=1)
            if not start:
                continue
            if stop <= start:
                stop = start + datetime.timedelta(minutes=1)
            p.set("start", _fmt(start))
            p.set("stop", _fmt(stop))
            prev_stop = stop
            changed += 1

        if prev_stop:
            finishes = [p for p in programmes if any(w in _txt(p, "title") for w in FINISHED_WORDS)]
            if finishes:
                finishes.sort(key=lambda p: _parse(p.get("start")) or datetime.datetime.max.replace(tzinfo=JST))
                f = finishes[0]
                f.set("start", _fmt(prev_stop))
                old_stop = _parse(f.get("stop"))
                if not old_stop or old_stop <= prev_stop:
                    f.set("stop", _fmt(prev_stop + datetime.timedelta(minutes=1)))

    if changed:
        if hasattr(ET, "indent"):
            ET.indent(tree, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
        print(f"EPG +1min switch applied: {changed} race blocks")


if sys.argv and str(sys.argv[0]).endswith("main_epg_3days.py"):
    atexit.register(_apply)
