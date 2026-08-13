import datetime
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))

JSON_OUT = Path("keiba_today.json")
M3U_OUT = Path("keiba_today.m3u")
MASTER_M3U = Path("keiba_master.m3u")
VERSION = "1.0-today"

LOCAL_CODES = {
    "帯広": 3,
    "門別": 36,
    "盛岡": 10,
    "水沢": 11,
    "浦和": 18,
    "船橋": 19,
    "大井": 20,
    "川崎": 21,
    "金沢": 22,
    "笠松": 23,
    "名古屋": 24,
    "園田": 27,
    "姫路": 28,
    "高知": 31,
    "佐賀": 32,
}

TVG_ID = {
    "帯広": "chihou.obihiro",
    "門別": "chihou.mombetsu",
    "盛岡": "chihou.morioka",
    "水沢": "chihou.mizusawa",
    "浦和": "chihou.urawa",
    "船橋": "chihou.funabashi",
    "大井": "chihou.oi",
    "川崎": "chihou.kawasaki_keiba",
    "金沢": "chihou.kanazawa",
    "笠松": "chihou.kasamatsu",
    "名古屋": "chihou.nagoya_keiba",
    "園田": "chihou.sonoda",
    "姫路": "chihou.himeji",
    "高知": "chihou.kochi_keiba",
    "佐賀": "chihou.saga",
}

NANKAN = {"浦和", "船橋", "大井", "川崎"}


class VisibleTextParser(HTMLParser):
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
        if self.skip:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.tokens.append(text)


def fetch_html(url, timeout=25):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "ja,en-US;q=0.8,en;q=0.6",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        raw = res.read()

    for enc in ("utf-8", "cp932", "shift_jis"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def visible_tokens(text):
    parser = VisibleTextParser()
    parser.feed(text)
    return parser.tokens


def hm_to_minutes(hm):
    h, m = map(int, hm.split(":"))
    return h * 60 + m


def detect_local_day_type(races):
    if not races:
        return "非開催"
    first = races[0].get("time", "")
    last = races[-1].get("time", "")
    if not first or not last:
        return "デイ"

    start = hm_to_minutes(first)
    end = hm_to_minutes(last)

    if end >= 19 * 60 + 30:
        return "ナイター"
    if end >= 17 * 60:
        return "薄暮"
    if start < 10 * 60:
        return "モーニング"
    return "デイ"


def classify_local_race(name="", kind_text="", conditions=""):
    text = f"{name} {kind_text} {conditions}".strip()

    if any(x in text for x in ["JpnⅠ","JpnI","JpnⅡ","JpnII","JpnⅢ","JpnIII"]):
        return {"race_type": "ダートグレード", "icon": "🏆"}
    if "準重賞" in text:
        return {"race_type": "準重賞", "icon": "⭐"}
    if "重賞" in text:
        return {"race_type": "重賞", "icon": "🏆"}
    if any(x in text for x in ["新馬", "フレッシュチャレンジ", "スーパーフレッシュチャレンジ"]):
        return {"race_type": "新馬", "icon": "🆕"}
    if "特別" in kind_text or any(x in name for x in ["特別", "賞", "杯", "カップ"]):
        return {"race_type": "特別", "icon": "🏇"}
    return {"race_type": "一般", "icon": "🐎"}


def normalize_local_race(race_no, time_text, race_name="", kind_text="", conditions=""):
    kind = classify_local_race(race_name, kind_text, conditions)
    return {
        "race": int(race_no),
        "time": time_text,
        "name": race_name.strip(),
        "kind": kind_text.strip(),
        "conditions": conditions.strip(),
        "race_type": kind["race_type"],
        "icon": kind["icon"],
        "main": False,
    }


def race_text(race):
    return " ".join(str(race.get(k, "")) for k in ("name", "kind", "conditions"))


def detect_main_race(races):
    if not races:
        return races

    for r in races:
        r["main"] = False

    grade_priority = [
        "JpnⅠ","JpnI","JpnⅡ","JpnII","JpnⅢ","JpnIII",
    ]
    for keyword in grade_priority:
        candidates = [r for r in races if keyword in race_text(r)]
        if candidates:
            candidates[-1]["main"] = True
            return races

    candidates = [r for r in races if r.get("race_type") in {"重賞", "ダートグレード", "準重賞"}]
    if candidates:
        candidates[-1]["main"] = True
        return races

    candidates = [r for r in races if r.get("race", 0) >= 7 and r.get("race_type") == "特別"]
    if candidates:
        candidates[-1]["main"] = True
        return races

    for r in races:
        if r.get("race") == 11:
            r["main"] = True
            return races

    (races[-2] if len(races) >= 2 else races[-1])["main"] = True
    return races


def prepare_venue(venue, races, source):
    races = sorted(races, key=lambda x: x["race"])
    races = detect_main_race(races)
    return {
        "source": source,
        "tvg_id": TVG_ID.get(venue, ""),
        "day_type": detect_local_day_type(races),
        "races": races,
    }


def fetch_hokkaido(date_str):
    races = []

    for race_no in range(1, 13):
        url = (
            "https://www.hokkaidokeiba.net/raceinfo/syuso.php?"
            + urllib.parse.urlencode({
                "p_day": date_str,
                "p_rno": f"{race_no:03d}",
            })
        )

        try:
            text = fetch_html(url, timeout=15)
        except Exception:
            if race_no == 1:
                return {}
            break

        visible = "\n".join(visible_tokens(text))

        tm = re.search(r"発走時刻[^0-9]*([0-2]?\d):([0-5]\d)", visible)
        if not tm:
            if race_no == 1:
                return {}
            break

        time_text = f"{int(tm.group(1)):02d}:{tm.group(2)}"

        title = ""
        title_match = re.search(r"第[０-９0-9]+競走\s+([^\n]+)", visible)
        if title_match:
            title = title_match.group(1).strip()

        condition = ""
        cond_match = re.search(r"（([^）]+)）", visible)
        if cond_match:
            condition = cond_match.group(1).strip()

        races.append(normalize_local_race(race_no, time_text, title, "", condition))

    if not races:
        return {}

    return {"門別": prepare_venue("門別", races, "ホッカイドウ競馬公式")}


def fetch_nar_venue(venue, baba_code, date_str, source_label="NAR公式"):
    date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
    date_param = date_obj.strftime("%Y/%m/%d")
    url = (
        "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?"
        + urllib.parse.urlencode({
            "k_babaCode": baba_code,
            "k_raceDate": date_param,
        })
    )

    try:
        page = fetch_html(url)
    except Exception:
        return None

    tokens = visible_tokens(page)
    text = "\n".join(tokens)

    if f"{venue}競馬" not in text and venue not in text:
        return None

    races = []
    i = 0
    while i < len(tokens):
        m = re.fullmatch(r"(\d{1,2})R", tokens[i])
        if not m:
            i += 1
            continue

        race_no = int(m.group(1))
        time_text = ""
        kind_text = ""
        race_name = ""

        j = i + 1
        while j < len(tokens) and j < i + 12:
            if re.fullmatch(r"\d{1,2}R", tokens[j]):
                break

            tm = re.fullmatch(r"([0-2]?\d):([0-5]\d)", tokens[j])
            if tm and not time_text:
                time_text = f"{int(tm.group(1)):02d}:{tm.group(2)}"
                j += 1
                continue

            if time_text:
                t = tokens[j]
                if t in {"有", "変更"}:
                    j += 1
                    continue
                if t in {"特別", "重賞", "準重賞"} and not kind_text:
                    kind_text = t
                    j += 1
                    continue
                if (
                    not race_name
                    and not re.search(r"(右|左)\d+m", t)
                    and t not in {"オッズ", "映像", "成績"}
                    and not t.isdigit()
                ):
                    race_name = t
                    break
            j += 1

        if time_text and race_name:
            races.append(normalize_local_race(race_no, time_text, race_name, kind_text, ""))

        i += 1

    unique = {}
    for race in races:
        unique.setdefault(race["race"], race)
    races = list(unique.values())

    if not races:
        return None

    return prepare_venue(venue, races, source_label)


def build_today(date_str):
    print(f"\n=== 地方競馬 TODAY V{VERSION} / {date_str} ===")

    data = {
        "date": date_str,
        "updated_at": datetime.datetime.now(JST).isoformat(),
        "source": "NAR / 各公式",
        "venues": {},
    }

    # 門別は専用公式
    hokkaido = fetch_hokkaido(date_str)
    data["venues"].update(hokkaido)

    # その他NAR
    for venue, code in LOCAL_CODES.items():
        if venue == "門別":
            continue
        source = "NAR公式（南関フォールバック）" if venue in NANKAN else "NAR公式"
        info = fetch_nar_venue(venue, code, date_str, source)
        if info:
            data["venues"][venue] = info

    for venue, info in data["venues"].items():
        print(f"  OK {venue}: {len(info.get('races', []))}R {info.get('day_type','')}")

    return data


def save_json(data):
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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

    master = parse_master_m3u(MASTER_M3U.read_text(encoding="utf-8-sig"))
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

    M3U_OUT.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    if missing:
        print("M3Uマスターに見つからない場:", ", ".join(missing))
    return True


def main():
    date_str = datetime.datetime.now(JST).strftime("%Y%m%d")
    data = build_today(date_str)
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
