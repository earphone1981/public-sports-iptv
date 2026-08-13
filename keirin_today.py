import datetime
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))

JSON_OUT = Path("keirin_today.json")
M3U_OUT = Path("keirin_today.m3u")
MASTER_M3U = Path("keirin_master.m3u")
VERSION = "4.0-today"

VENUES = {
    "函館": "11", "青森": "12", "いわき平": "13", "弥彦": "21", "前橋": "22",
    "取手": "23", "宇都宮": "24", "大宮": "25", "西武園": "26", "京王閣": "27",
    "立川": "28", "松戸": "31", "千葉": "32", "川崎": "34", "平塚": "35",
    "小田原": "36", "伊東": "37", "静岡": "38", "名古屋": "42", "岐阜": "43",
    "大垣": "44", "豊橋": "45", "富山": "46", "松阪": "47", "四日市": "48",
    "福井": "51", "奈良": "53", "向日町": "54", "和歌山": "55", "岸和田": "56",
    "玉野": "61", "広島": "62", "防府": "63", "高松": "71", "小松島": "73",
    "高知": "74", "松山": "75", "小倉": "81", "久留米": "83", "武雄": "84",
    "佐世保": "85", "別府": "86", "熊本": "87",
}

TVG_ID = {
    "函館": "keirin.hakodate", "青森": "keirin.aomori", "いわき平": "keirin.iwakitaira",
    "弥彦": "keirin.yahiko", "前橋": "keirin.maebashi", "取手": "keirin.toride",
    "宇都宮": "keirin.utsunomiya", "大宮": "keirin.omiya", "西武園": "keirin.seibuen",
    "京王閣": "keirin.keiogatsu", "立川": "keirin.tachikawa", "松戸": "keirin.matsudo",
    "千葉": "keirin.pist6", "川崎": "keirin.kawasaki", "平塚": "keirin.hiratsuka",
    "小田原": "keirin.odawara", "伊東": "keirin.ito", "静岡": "keirin.shizuoka",
    "名古屋": "keirin.nagoya", "岐阜": "keirin.gifu", "大垣": "keirin.ogaki",
    "豊橋": "keirin.toyohashi", "富山": "keirin.toyama", "松阪": "keirin.matsusaka",
    "四日市": "keirin.yokkaichi", "福井": "keirin.fukui", "奈良": "keirin.nara",
    "向日町": "keirin.mukomachi", "和歌山": "keirin.wakayama", "岸和田": "keirin.kishiwada",
    "玉野": "keirin.tamano", "広島": "keirin.hiroshima", "防府": "keirin.hofu",
    "高松": "keirin.takamatsu", "小松島": "keirin.komatsushima", "高知": "keirin.kochi",
    "松山": "keirin.matsuyama", "小倉": "keirin.kokura", "久留米": "keirin.kurume",
    "武雄": "keirin.takeo", "佐世保": "keirin.sasebo", "別府": "keirin.beppu",
    "熊本": "keirin.kumamoto",
}

SPECIAL_RACE_ALIASES = {
    "Ｓ級ＯＲＩ": "オリオン賞レース",
    "S級ORI": "オリオン賞レース",
    "Ｓ級ＤＲＭ": "ドリームレース",
    "S級DRM": "ドリームレース",
}


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
        t = re.sub(r"\s+", " ", data).strip()
        if t:
            self.tokens.append(t)


def fetch_html(url, timeout=10):
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


def tokens_of(text):
    p = VisibleTextParser()
    p.feed(text)
    return p.tokens


def expand_race_name(name):
    raw = (name or "").strip()
    return SPECIAL_RACE_ALIASES.get(raw, raw)


def normalize_grade(text):
    text = text or ""
    patterns = [
        (r"\bG[ⅠI1]\b|Ｇ[ⅠI1]", "GI"),
        (r"\bG[ⅡI2]\b|Ｇ[ⅡI2]", "GII"),
        (r"\bG[ⅢI3]\b|Ｇ[ⅢI3]", "GIII"),
        (r"\bF[ⅠI1]\b|Ｆ[ⅠI1]", "FI"),
        (r"\bF[ⅡI2]\b|Ｆ[ⅡI2]", "FII"),
    ]
    for pat, label in patterns:
        if re.search(pat, text, flags=re.I):
            return label
    return ""


def normalize_day_type(text, first_time=""):
    if "ミッドナイト" in text:
        return "ミッドナイト", "⭐"
    if "モーニング" in text:
        return "モーニング", "🌅"
    if "ナイター" in text:
        return "ナイター", "🌙"

    if first_time:
        h = int(first_time.split(":")[0])
        if h < 10:
            return "モーニング", "🌅"
        if h >= 20:
            return "ミッドナイト", "⭐"
        if h >= 15:
            return "ナイター", "🌙"
    return "デイ", "☀️"


def classify_race(name):
    text = expand_race_name(name or "")
    if any(x in text for x in ("Ｌ級", "L級", "ガールズ", "ガ予", "ガ決")):
        race_class, icon = "ガールズ", "💛"
    elif "Ｓ級" in text or "S級" in text:
        race_class, icon = "S級", "🚲"
    elif "Ａ級" in text or "A級" in text:
        race_class, icon = "A級", "🚲"
    else:
        race_class, icon = "競輪", "🚲"

    is_semi = ("準決勝" in text or "準決" in text)
    is_final = (("決勝" in text or "優勝" in text or "決　勝" in text) and not is_semi)
    return {
        "race_class": race_class,
        "icon": icon,
        "girls": race_class == "ガールズ",
        "is_final": is_final,
        "is_semi": is_semi,
        "is_special": any(x in text for x in ("特選", "初特選", "オリオン賞", "ドリームレース")),
    }


def detect_main_race(races):
    for r in races:
        r["main"] = False
    special = [r for r in races if any(
        k in expand_race_name(r.get("name", ""))
        for k in ("オリオン賞レース", "ドリームレース")
    )]
    if special:
        special[-1]["main"] = True
    else:
        finals = [r for r in races if r.get("is_final")]
        (finals[-1] if finals else races[-1])["main"] = True
    return races


def clean_event_name(name, venue=""):
    s = re.sub(r"\s+", " ", (name or "")).strip()
    if not s:
        return ""
    for pat in (
        r"前検日コメなら", r"前検日コメントなら", r"前検日コメント", r"前検日コメ",
        r"開催日(?:程)?", r"レース一覧", r"レース情報", r"出走表", r"オッズ",
        r"結果", r"レース映像", r"投票",
    ):
        s = re.sub(pat, " ", s, flags=re.I)
    if venue:
        s = re.sub(rf"{re.escape(venue)}競輪場", " ", s)
        s = re.sub(rf"{re.escape(venue)}競輪", " ", s)
    s = re.sub(r"(^|\s)(GI|GII|GIII|FI|FII|ＧⅠ|ＧⅡ|ＧⅢ|ＦⅠ|ＦⅡ)(?=\s|$)", " ", s, flags=re.I)
    s = re.sub(r"\d{4}年\d{1,2}月\d{1,2}日(?:\([^)]*\))?", " ", s)
    s = re.sub(r"(初日|2日目|3日目|4日目|5日目|最終日)", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -　")


def parse_mobile_page(venue, code, date_str, retries=3):
    url = f"https://sp.oddspark.com/keirin/SpRaceList.do?joCd={code}&kaisaiBi={date_str}"

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            tokens = tokens_of(fetch_html(url, timeout=15))
            text = "\n".join(tokens)

            d = datetime.datetime.strptime(date_str, "%Y%m%d")
            date_label = f"{d.year}年{d.month}月{d.day}日"

            if venue not in text or date_label not in text:
                raise RuntimeError("場名/日付が見つからない")

            if not any(re.fullmatch(r"\d{1,2}R", t) for t in tokens):
                raise RuntimeError("レース行が見つからない")

            event_day = ""
            event_name = ""

            for i, t in enumerate(tokens):
                if t in ("初日", "2日目", "3日目", "4日目", "5日目", "最終日"):
                    event_day = t
                    for cand in tokens[i + 1:min(i + 6, len(tokens))]:
                        if (
                            cand not in {"投票", "出走表", "オッズ", "結果", "レース映像"}
                            and not re.fullmatch(r"\d{1,2}R", cand)
                            and len(cand) >= 2
                        ):
                            event_name = clean_event_name(cand, venue)
                            break
                    break

            races = []
            for i, tok in enumerate(tokens):
                m = re.fullmatch(r"(\d{1,2})R", tok)
                if not m:
                    continue

                race_no = int(m.group(1))
                race_name = ""
                cutoff = ""

                for t in tokens[i + 1:min(i + 8, len(tokens))]:
                    cm = re.search(r"([0-2]?\d):([0-5]\d)締切", t)
                    if cm:
                        cutoff = f"{int(cm.group(1)):02d}:{cm.group(2)}"

                    if re.fullmatch(r"[ＡAＳSＬL]級.+", t):
                        race_name = t.strip()

                if race_name:
                    races.append({
                        "race": race_no,
                        "name": race_name,
                        "cutoff": cutoff,
                    })

            if not races:
                raise RuntimeError("レース情報を抽出できない")

            if attempt > 1:
                print(f"  RETRY OK {venue}: {attempt}回目で取得成功")

            return {
                "venue": venue,
                "code": code,
                "event_day": event_day,
                "event_name": event_name,
                "races": races,
            }

        except Exception as e:
            last_error = e
            if attempt < retries:
                time.sleep(1.5 * attempt)

    print(f"  WARN {venue}: {retries}回取得失敗 ({last_error})")
    return None

def fetch_exact_race(venue, code, date_str, race, retries=2):
    race_no = race["race"]
    url = f"https://www.oddspark.com/keirin/RaceList.do?joCode={code}&kaisaiBi={date_str}&raceNo={race_no}"

    tokens = None
    for attempt in range(1, retries + 1):
        try:
            tokens = tokens_of(fetch_html(url, timeout=15))
            break
        except Exception:
            if attempt < retries:
                time.sleep(0.8 * attempt)

    if tokens is None:
        return race

    text = "\n".join(tokens)
    tm = re.search(r"発走時間\s*([0-2]?\d):([0-5]\d)", text)
    if tm:
        race["time"] = f"{int(tm.group(1)):02d}:{tm.group(2)}"
    elif race.get("cutoff"):
        h, m = map(int, race["cutoff"].split(":"))
        mins = h * 60 + m + 5
        race["time"] = f"{(mins // 60) % 24:02d}:{mins % 60:02d}"
        race["time_inferred"] = True

    for label in ("モーニング", "ナイター", "ミッドナイト"):
        if label in text:
            race["day_type_raw"] = label
            break

    nm = re.search(r"第\d+レース\s*\(([^)]+)\)", text)
    race["name_raw"] = nm.group(1).strip() if nm else race.get("name", "")
    race["name"] = expand_race_name(race["name_raw"])

    dm = re.search(
        r"\d{4}年\d{1,2}月\d{1,2}日\([^)]*\)\s*(初日|2日目|3日目|4日目|5日目|最終日)",
        text,
    )
    if dm:
        race["event_day_detail"] = dm.group(1)

    header_candidates = [t for t in tokens[:120] if (venue in t and "競輪場" in t) or any(
        x in t for x in ("GI", "GII", "GIII", "FI", "FII", "ＧⅠ", "ＧⅡ", "ＧⅢ", "ＦⅠ", "ＦⅡ")
    )]
    grade = normalize_grade(" ".join(header_candidates))
    if grade:
        race["grade"] = grade

    event_name = ""
    for t in tokens[:100]:
        if venue in t and "競輪場" in t:
            cleaned = re.sub(rf"^.*?{re.escape(venue)}競輪場\s*", "", t).strip()
            cleaned = re.sub(r"^(GI|GII|GIII|FI|FII|ＧⅠ|ＧⅡ|ＧⅢ|ＦⅠ|ＦⅡ)\s*", "", cleaned).strip()
            event_name = clean_event_name(cleaned, venue)
            if event_name:
                break
    if event_name:
        race["event_name_detail"] = event_name

    cls = classify_race(race["name"])
    if cls["race_class"] == "競輪" and race.get("grade", "") in {"GI", "GII", "GIII"}:
        cls["race_class"] = "S級"
    race.update(cls)
    race["url"] = url
    return race


def build_today(date_str):
    print(f"\n=== 競輪 TODAY V{VERSION} / {date_str} ===")
    active = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(parse_mobile_page, v, c, date_str): v for v, c in VENUES.items()}
        for fut in as_completed(futures):
            try:
                info = fut.result()
            except Exception:
                info = None
            if info:
                active.append(info)
                print(f"  {info['venue']}: 開催あり")

    active.sort(key=lambda x: int(x["code"]))
    data = {
        "date": date_str,
        "updated_at": datetime.datetime.now(JST).isoformat(),
        "source": "OddsPark",
        "venues": {},
    }

    for info in active:
        venue, code = info["venue"], info["code"]
        exact = []
        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = [ex.submit(fetch_exact_race, venue, code, date_str, dict(r)) for r in info["races"]]
            for fut in futures:
                try:
                    exact.append(fut.result())
                except Exception:
                    pass
        exact = sorted([r for r in exact if r.get("time")], key=lambda r: r["race"])
        if not exact:
            continue

        event_name = next((r.get("event_name_detail") for r in exact if r.get("event_name_detail")), info.get("event_name", ""))
        event_name = clean_event_name(event_name, venue)
        event_day = next((r.get("event_day_detail") for r in exact if r.get("event_day_detail")), info.get("event_day", ""))
        grade = next((r.get("grade") for r in exact if r.get("grade")), "")
        day_type, day_emoji = normalize_day_type(" ".join(r.get("day_type_raw", "") for r in exact), exact[0]["time"])
        exact = detect_main_race(exact)

        data["venues"][venue] = {
            "source": "オッズパーク競輪",
            "tvg_id": TVG_ID.get(venue, ""),
            "event_day": event_day,
            "event_name": event_name,
            "grade": grade,
            "day_type": day_type,
            "day_emoji": day_emoji,
            "races": exact,
        }
        print(f"  OK {venue}: {len(exact)}R {day_emoji}{day_type} {grade} {event_name} {event_day}")

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
        print(f"\n注意: {MASTER_M3U} がありません。")
        print("送ってもらった固定競輪M3Uを keirin_master.m3u の名前で同じフォルダに保存してください。")
        return False

    master = parse_master_m3u(MASTER_M3U.read_text(encoding="utf-8-sig"))
    out = ["#EXTM3U"]
    missing = []

    for venue, info in data["venues"].items():
        tvg_id = info.get("tvg_id", "")
        if tvg_id in master:
            extinf, url = master[tvg_id]
            # 表示名末尾の「2」などは残さず、当日版は場名で統一
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
