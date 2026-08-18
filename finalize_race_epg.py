from pathlib import Path
import datetime
import re
import xml.etree.ElementTree as ET

JST = datetime.timezone(datetime.timedelta(hours=9))
TARGET_PREFIXES = ("keirin.", "chihou.", "keiba.", "auto.", "boat.", "jra.east", "jra.west", "jra.hokkaido")


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
    return cid.startswith(TARGET_PREFIXES[:-3]) or cid in TARGET_PREFIXES[-3:]


def race_clock(title):
    t = str(title or "")
    m = re.search(r"(?<!\d)(\d{1,2}):(\d{2})\s*発走", t)
    if not m:
        return None
    h, minute = map(int, m.groups())
    if 0 <= h <= 23 and 0 <= minute <= 59:
        return h, minute
    return None


def resolve_race_time(programme):
    title = programme.findtext("title") or ""
    hm = race_clock(title)
    start = parse_xmltv(programme.get("start"))
    if hm is None or start is None:
        return None

    h, minute = hm
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

    by_channel = {}
    for p in root.findall("programme"):
        cid = p.get("channel", "")
        if not is_target(cid):
            continue
        rt = resolve_race_time(p)
        if rt is None:
            continue
        by_channel.setdefault(cid, []).append((rt, p))

    adjusted = 0
    for cid, items in by_channel.items():
        items.sort(key=lambda x: x[0])

        # 日付単位で処理。各レース表示は「前レース発走1分後」から
        # 「自レース発走1分後」までにする。
        groups = {}
        for rt, p in items:
            # 早朝レースは前日開催の続きになり得るので、4時未満は前日扱い。
            key = rt.date() if rt.hour >= 4 else (rt.date() - datetime.timedelta(days=1))
            groups.setdefault(key, []).append((rt, p))

        for _, races in groups.items():
            races.sort(key=lambda x: x[0])
            previous_cut = None
            for rt, p in races:
                own_cut = rt + datetime.timedelta(minutes=1)
                old_start = parse_xmltv(p.get("start"))
                old_stop = parse_xmltv(p.get("stop"))

                if previous_cut is not None:
                    new_start = previous_cut
                else:
                    new_start = old_start

                # 最初のRは元の開始時刻を維持。以降は前Rの発走1分後に切替。
                if new_start is not None and new_start < own_cut:
                    p.set("start", fmt_xmltv(new_start))
                    p.set("stop", fmt_xmltv(own_cut))
                    adjusted += 1
                elif old_start is not None and old_stop is not None:
                    # 異常データ時は元の時間を壊さない。
                    pass

                previous_cut = own_cut

    ET.indent(tree, space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print(f"Race EPG timing finalized: {adjusted}")


if __name__ == "__main__":
    main()
