import datetime
import html
import json
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))
OUT = Path("jra_today.json")
VERSION = "1.0"

JRA_VENUES = ["札幌","函館","福島","新潟","東京","中山","中京","京都","阪神","小倉"]

CHANNEL_BY_VENUE = {
    "札幌": "hokkaido",
    "函館": "hokkaido",
    "福島": "east",
    "新潟": "east",
    "東京": "east",
    "中山": "east",
    "中京": "west",
    "京都": "west",
    "阪神": "west",
    "小倉": "west",
}

TVG_ID = {
    "gch": "jra.gch",
    "east": "jra.east",
    "west": "jra.west",
    "hokkaido": "jra.hokkaido",
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

def visible_tokens(source):
    p = VisibleTextParser()
    p.feed(source)
    return p.tokens

def classify_jra_race(name="", conditions=""):
    text = f"{name} {conditions}".strip()
    if "障害" in text and any(x in text for x in ["J・GⅠ","J・GI","J・GⅡ","J・GII","J・GⅢ","J・GIII"]):
        return {"race_type":"障害重賞","icon":"🏆🚧"}
    if "障害" in text:
        return {"race_type":"障害","icon":"🚧"}
    if "メイクデビュー" in text or "新馬" in text:
        return {"race_type":"新馬","icon":"🆕"}
    if any(x in text for x in ["GⅠ","GI","GⅡ","GII","GⅢ","GIII"]):
        return {"race_type":"重賞","icon":"🏆"}
    if "リステッド" in text or "(L)" in text or "（L）" in text:
        return {"race_type":"リステッド","icon":"⭐"}
    if "オープン" in text:
        return {"race_type":"オープン","icon":"⭐"}
    if any(x in text for x in ["特別","ステークス","カップ","賞"]):
        return {"race_type":"特別","icon":"🏇"}
    return {"race_type":"一般","icon":"🐎"}

def race_text(r):
    return f"{r.get('name','')} {r.get('conditions','')}".strip()

def detect_main_race(races):
    for r in races:
        r["main"] = False
    priorities = ["J・GⅠ","J・GI","GⅠ","GI","J・GⅡ","J・GII","GⅡ","GII","J・GⅢ","J・GIII","GⅢ","GIII"]
    for kw in priorities:
        c = [r for r in races if kw in race_text(r)]
        if c:
            c[-1]["main"] = True
            return races
    c = [r for r in races if r.get("race_type") in {"重賞","障害重賞","リステッド"}]
    if c:
        c[-1]["main"] = True
        return races
    for r in races:
        if r.get("race") == 11:
            r["main"] = True
            return races
    if races:
        races[-1]["main"] = True
    return races

def normalize_race(race_no, time_text, race_name="", conditions=""):
    kind = classify_jra_race(race_name, conditions)
    return {
        "race": int(race_no),
        "time": time_text,
        "name": race_name.strip(),
        "conditions": conditions.strip(),
        "race_type": kind["race_type"],
        "icon": kind["icon"],
        "main": False,
    }

VENUE_HEADER_RE = re.compile(r"\d+回(" + "|".join(map(re.escape, JRA_VENUES)) + r")\d+日")
RACE_RE = re.compile(r"^(\d{1,2})レース$")
TIME_RE = re.compile(r"^(\d{1,2})時(\d{2})分$")

def split_name_conditions(text):
    text = html.unescape(re.sub(r"\s+", " ", text).strip())
    if re.match(r"^\d歳", text) or text.startswith("障害"):
        return text, text
    m = re.search(r"\s(?=\d歳(?:以上)?(?:未勝利|新馬|以上|オープン|\d勝クラス))", text)
    if m:
        return text[:m.start()].strip() or text, text[m.start():].strip()
    return text, text

def fetch_jra(date_str):
    result = {}
    dt = datetime.datetime.strptime(date_str, "%Y%m%d")
    url = f"https://www.jra.go.jp/keiba/calendar{dt.year}/{dt.year}/{dt.month}/{dt.strftime('%m%d')}.html"
    print("JRA公式:", url)

    try:
        page = fetch_html(url)
    except Exception as e:
        print("JRA取得失敗:", e)
        return result

    tokens = visible_tokens(page)
    current_venue = None
    current_races = []

    def flush():
        nonlocal current_venue, current_races
        if current_venue and current_races:
            current_races.sort(key=lambda x: x["race"])
            result[current_venue] = {
                "source": "JRA公式",
                "channel": CHANNEL_BY_VENUE[current_venue],
                "tvg_id": TVG_ID[CHANNEL_BY_VENUE[current_venue]],
                "races": detect_main_race(current_races),
            }
        current_venue = None
        current_races = []

    i = 0
    while i < len(tokens):
        token = tokens[i]
        vm = VENUE_HEADER_RE.search(token)
        if vm:
            flush()
            current_venue = vm.group(1)
            i += 1
            continue

        rm = RACE_RE.match(token)
        if rm and current_venue:
            race_no = int(rm.group(1))
            parts = []
            time_text = None
            j = i + 1

            while j < len(tokens) and j < i + 30:
                t = tokens[j]
                if VENUE_HEADER_RE.search(t) or RACE_RE.match(t):
                    break
                tm = TIME_RE.match(t)
                if tm:
                    time_text = f"{int(tm.group(1)):02d}:{tm.group(2)}"
                    break
                if t not in {"レース番号","レース名・条件","発走時刻"}:
                    parts.append(t)
                j += 1

            if time_text:
                full = " ".join(parts)
                name, cond = split_name_conditions(full)
                current_races.append(normalize_race(race_no, time_text, name, cond))
                i = j

        i += 1

    flush()
    return result

def fetch_greenchannel(retries=4):
    """
    グリーンチャンネル公式「日別番組表」を取得。
    一時的な混雑表示や通信失敗を考慮し、数回リトライする。
    それでも取得できない場合は空配列を返し、EPG側で待機表示にフォールバック。
    """
    url = "https://www.greenchannel.jp/daily-timetable.html"
    last_error = ""

    for attempt in range(1, retries + 1):
        try:
            page = fetch_html(url, timeout=25)
        except Exception as e:
            last_error = f"通信失敗: {e}"
            print(f"GCH番組表 {attempt}/{retries}: {last_error}")
            if attempt < retries:
                time.sleep(5 * attempt)
            continue

        tokens = visible_tokens(page)
        joined = "\n".join(tokens)

        if "現在アクセスが集中しているため表示できません" in joined:
            last_error = "公式番組表が混雑表示"
            print(f"GCH番組表 {attempt}/{retries}: {last_error}")
            if attempt < retries:
                time.sleep(5 * attempt)
            continue

        programs = []

        # 例:
        # 06:30～07:00
        # 番組名
        time_pat = re.compile(
            r"^([0-2]?\d):([0-5]\d)\s*[～〜~\-]\s*([0-2]?\d):([0-5]\d)$"
        )

        for i, t in enumerate(tokens):
            m = time_pat.match(t.strip())
            if not m:
                continue

            start_hm = f"{int(m.group(1)):02d}:{m.group(2)}"
            stop_hm = f"{int(m.group(3)):02d}:{m.group(4)}"

            title = ""
            for cand in tokens[i + 1:i + 8]:
                c = re.sub(r"\s+", " ", cand).strip()

                if not c:
                    continue

                if time_pat.match(c):
                    break

                if c in {
                    "番組表（日別）",
                    "日別番組表",
                    "週別番組表",
                    "番組表",
                    "放送スケジュール",
                }:
                    continue

                # ナビゲーション系の短い語は除外
                if c in {"トップ", "番組", "競馬", "ニュース", "検索"}:
                    continue

                title = c
                break

            if title:
                programs.append(
                    {
                        "start": start_hm,
                        "stop": stop_hm,
                        "title": title,
                    }
                )

        # 重複除去
        unique = []
        seen = set()
        for p in programs:
            key = (p["start"], p["stop"], p["title"])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        if unique:
            print(
                f"GCH番組表 {attempt}/{retries}: OK "
                f"{len(unique)}番組"
            )
            return {
                "source": "グリーンチャンネル公式",
                "url": url,
                "ok": True,
                "programs": unique,
                "error": "",
                "attempts": attempt,
            }

        last_error = "番組行を抽出できませんでした"
        print(f"GCH番組表 {attempt}/{retries}: {last_error}")

        if attempt < retries:
            time.sleep(5 * attempt)

    return {
        "source": "グリーンチャンネル公式",
        "url": url,
        "ok": False,
        "programs": [],
        "error": last_error or "取得失敗",
        "attempts": retries,
    }

def main():
    date_str = datetime.datetime.now(JST).strftime("%Y%m%d")
    venues = fetch_jra(date_str)

    channels = {"east": [], "west": [], "hokkaido": []}
    for venue, info in venues.items():
        channels[info["channel"]].append(venue)

    data = {
        "date": date_str,
        "updated_at": datetime.datetime.now(JST).isoformat(),
        "venues": venues,
        "channels": channels,
        "greenchannel": fetch_greenchannel(),
    }

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("")
    print("============================")
    print("中央競馬データ取得")
    print("日付:", date_str)
    print("開催場:", ", ".join(venues) if venues else "なし")
    print("EAST:", ", ".join(channels["east"]) or "非開催")
    print("WEST:", ", ".join(channels["west"]) or "非開催")
    print("HOKKAIDO:", ", ".join(channels["hokkaido"]) or "非開催")
    print("GCH公式番組表:", "OK" if data["greenchannel"]["ok"] else "取得待ち")
    print("JSON:", OUT)
    print("============================")

if __name__ == "__main__":
    main()
