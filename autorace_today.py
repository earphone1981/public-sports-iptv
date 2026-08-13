import datetime
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))

JSON_OUT = Path("autorace_today.json")
M3U_OUT = Path("autorace_today.m3u")
MASTER_M3U = Path("autorace_master.m3u")
VERSION = "3.0-today"

VENUES = {
    "川口": "02",
    "伊勢崎": "03",
    "浜松": "04",
    "飯塚": "05",
    "山陽": "06",
}

TVG_ID = {
    "川口": "auto.kawaguchi",
    "伊勢崎": "auto.isesaki",
    "浜松": "auto.hamamatsu",
    "飯塚": "auto.iizuka",
    "山陽": "auto.sanyo",
}


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            t = re.sub(r"\s+", " ", data).strip()
            if t:
                self.tokens.append(t)


def fetch(url, timeout=15):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "ja",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()

    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def tokens(html):
    p = Parser()
    p.feed(html)
    return p.tokens


def grade_of(text):
    t = text.upper().replace("Ｇ", "G").replace("Ｓ", "S")
    if re.search(r"\bSG\b", t):
        return "SG"
    if re.search(r"\bG(?:I|1)\b", t) or "GⅠ" in t:
        return "GI"
    if re.search(r"\bG(?:II|2)\b", t) or "GⅡ" in t:
        return "GII"
    return ""


def race_kind(name):
    if "優勝戦" in name:
        return "優勝戦", "🏆", True
    if "準決勝" in name:
        return "準決勝", "🔥", False
    if "準々決勝" in name:
        return "準々決勝", "🔥", False
    if "特別選抜" in name:
        return "特別選抜戦", "⭐", False
    if "選抜" in name:
        return "選抜戦", "⭐", False
    if "予選" in name:
        return "予選", "🏍️", False
    return "一般戦", "🏍️", False


def day_type(text, first, last):
    for key, label, icon in [
        ("オーバーミッドナイト", "オーバーミッドナイト", "🌌"),
        ("ミッドナイト", "ミッドナイト", "⭐"),
        ("アフター５", "アフター5", "🌆"),
        ("アフター5", "アフター5", "🌆"),
        ("ナイター", "ナイター", "🌙"),
        ("ナイトレース", "ナイトレース", "🌙"),
        ("アーリー", "アーリー", "🌅"),
    ]:
        if key in text:
            return label, icon

    sh = int(first[:2])
    eh = int(last[:2])

    if sh >= 20:
        return "ミッドナイト", "⭐"
    if sh >= 17:
        return "アフター5", "🌆"
    if eh >= 20:
        return "ナイター", "🌙"
    return "デイ", "☀️"


def get_race(venue, code, date, no):
    url = (
        "https://www.oddspark.com/autorace/Odds.do"
        f"?placeCd={code}&raceDy={date}&raceNo={no}"
    )

    try:
        ts = tokens(fetch(url))
    except Exception:
        return None

    text = "\n".join(ts)

    if f"R{no}" not in text or "発走時間" not in text:
        return None

    tm = re.search(r"発走時間\s*([0-2]?\d):([0-5]\d)", text)
    if not tm:
        return None

    rt = ""
    for i, t in enumerate(ts):
        if re.search(rf"R\s*{no}$", t):
            for x in ts[i + 1:i + 8]:
                m = re.match(r"(.+?)\s+3100m", x)
                if m:
                    rt = m.group(1).strip()
                    break

    if not rt:
        m = re.search(r"\n([^\n]+?)\s+3100m\(", text)
        if m:
            rt = m.group(1).strip()

    if not rt:
        rt = f"{no}R"

    kind, icon, is_final = race_kind(rt)

    return {
        "race": no,
        "time": f"{int(tm.group(1)):02d}:{tm.group(2)}",
        "name": rt,
        "race_type": kind,
        "icon": icon,
        "is_final": is_final,
        "is_semi": "準決勝" in rt,
        "main": False,
        "url": url,
        "_page_text": text,
    }


def clean_event_name(name, venue=""):
    s = re.sub(r"\s+", " ", (name or "")).strip()
    if not s:
        return ""

    s = re.sub(r"開催日（?[^）)]*）?", " ", s)
    s = re.sub(
        r"\d{4}年\d{1,2}月\d{1,2}日(?:（[^）]+）|\([^)]*\))?",
        " ",
        s,
    )

    for noise in (
        "レース一覧",
        "レース情報",
        "オッズパークオートレース",
        "オッズパーク",
        "出走表",
        "オッズ",
        "結果",
        "投票",
    ):
        s = s.replace(noise, " ")

    if venue:
        s = s.replace(f"{venue}｜", " ")
        s = s.replace(f"{venue}|", " ")
        s = s.replace(venue, " ")

    s = re.sub(r"[|｜]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -　")

    if s in {"開催", "開催日", "レース"}:
        return ""

    return s


def get_venue(venue, code, date):
    list_url = (
        "https://sp.oddspark.com/autorace/SpRaceList.do"
        f"?joCd={code}&joCode={code}&kaisaiBi={date}&raceNo="
    )

    try:
        lt = tokens(fetch(list_url))
        list_text = "\n".join(lt)
    except Exception:
        return None

    y = int(date[:4])
    m = int(date[4:6])
    d = int(date[6:8])

    if venue not in list_text or f"{y}年{m}月{d}日" not in list_text:
        return None

    if not re.search(r"(?:^|\n)1R(?:\n|$)", list_text):
        return None

    races = []
    for no in range(1, 13):
        r = get_race(venue, code, date, no)
        if r:
            races.append(r)

    if not races:
        return None

    all_text = list_text + "\n" + races[0]["_page_text"]

    event_day = ""
    for x in ("初日", "2日目", "3日目", "4日目", "5日目", "6日目", "最終日"):
        if x in all_text:
            event_day = x
            break

    event_name = ""
    for t in lt:
        if venue in t and ("市営" in t or "開催" in t):
            event_name = t
            break

    if not event_name:
        m = re.search(r"(令和[^\n]+(?:開催|～)[^\n]*)", all_text)
        if m:
            event_name = m.group(1).strip()

    event_name = clean_event_name(event_name, venue)

    grade = grade_of(all_text)
    dtype, dicon = day_type(all_text, races[0]["time"], races[-1]["time"])

    for r in races:
        r.pop("_page_text", None)

    finals = [r for r in races if r["is_final"]]
    (finals[-1] if finals else races[-1])["main"] = True

    return {
        "source": "オッズパークオート",
        "tvg_id": TVG_ID[venue],
        "event_name": event_name,
        "event_day": event_day,
        "grade": grade,
        "day_type": dtype,
        "day_emoji": dicon,
        "races": races,
        "url": list_url,
    }


def build_today(date):
    print(f"\n=== オートレース TODAY V{VERSION} / {date} ===")

    out = {
        "date": date,
        "updated_at": datetime.datetime.now(JST).isoformat(),
        "source": "OddsPark Auto",
        "venues": {},
    }

    for venue, code in VENUES.items():
        print(f"CHECK {venue} ...", end="", flush=True)

        info = get_venue(venue, code, date)
        if not info:
            print(" 非開催")
            continue

        out["venues"][venue] = info

        meta = " ".join(
            x
            for x in (
                info["grade"],
                info["event_name"],
                info["event_day"],
            )
            if x
        )

        print(
            f" OK {len(info['races'])}R "
            f"{info['day_emoji']}{info['day_type']}"
            + (f" [{meta}]" if meta else "")
        )

        for r in info["races"]:
            print(
                f"  {r['icon']} {r['race']}R {r['time']} {r['name']}"
                + (" 🏆MAIN" if r["main"] else "")
            )

    return out


def save_json(data):
    JSON_OUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_master_m3u(text):
    entries = {}
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            m = re.search(r'tvg-id="([^"]+)"', line)
            url = ""

            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()

                if nxt and not nxt.startswith("#"):
                    url = nxt
                    break

                if nxt.startswith("#EXTINF:"):
                    break

                j += 1

            if m and url:
                entries[m.group(1)] = (line, url)

        i += 1

    return entries


def build_today_m3u(data):
    if not MASTER_M3U.exists():
        print(f"注意: {MASTER_M3U} がありません")
        return False

    master = parse_master_m3u(
        MASTER_M3U.read_text(encoding="utf-8-sig")
    )

    out = ["#EXTM3U"]
    missing = []

    for venue, info in data["venues"].items():
        tvg_id = info.get("tvg_id", "")

        if tvg_id in master:
            extinf, url = master[tvg_id]
            extinf = re.sub(r",.*$", f",{venue}", extinf)
            out.extend([extinf, url, ""])
        else:
            missing.append(f"{venue} ({tvg_id})")

    M3U_OUT.write_text(
        "\n".join(out).rstrip() + "\n",
        encoding="utf-8",
    )

    if missing:
        print("M3Uマスターに見つからない場:", ", ".join(missing))

    return True


def main():
    date = datetime.datetime.now(JST).strftime("%Y%m%d")

    data = build_today(date)
    save_json(data)
    m3u_ok = build_today_m3u(data)

    print("\n============================")
    print(f"日付: {data['date']}")
    print(f"開催場数: {len(data['venues'])}")
    print(f"JSON: {JSON_OUT}")
    print(f"M3U: {M3U_OUT if m3u_ok else '未生成'}")
    print("============================")


if __name__ == "__main__":
    main()
