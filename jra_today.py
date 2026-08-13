import datetime
import html
import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))
OUT = Path("jra_today.json")

NETKEIBA_LIST = "https://race.netkeiba.com/top/race_list.html?kaisai_date={date}"
JCOM_SEARCH = (
    "https://tvguide.myjcom.jp/search/event/"
    "?channel=164_65406&channelType=120"
)

VENUE_CODE = {
    "01": "札幌",
    "02": "函館",
    "03": "福島",
    "04": "新潟",
    "05": "東京",
    "06": "中山",
    "07": "中京",
    "08": "京都",
    "09": "阪神",
    "10": "小倉",
}

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
    "east": "jra.east",
    "west": "jra.west",
    "hokkaido": "jra.hokkaido",
    "gch": "jra.gch",
}


class TextParser(HTMLParser):
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


def fetch(url, timeout=25):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.5",
            "Cache-Control": "no-cache",
            "Referer": "https://www.google.com/",
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


def visible_tokens(source):
    p = TextParser()
    p.feed(source)
    return p.tokens


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(str(s or ""))).strip()


def classify(name):
    t = name or ""
    if "障害" in t:
        return "障害", "🚧"
    if any(x in t for x in ("GⅠ", "GI", "GⅡ", "GII", "GⅢ", "GIII")):
        return "重賞", "🏆"
    if "新馬" in t or "メイクデビュー" in t:
        return "新馬", "🆕"
    if "オープン" in t:
        return "オープン", "⭐"
    if any(x in t for x in ("特別", "ステークス", "カップ", "賞")):
        return "特別", "🏇"
    return "一般", "🐎"


def extract_netkeiba_race_ids(source, date_str):
    # race_idは通常12桁。ページ内のリンク・JS双方を拾う。
    ids = set(re.findall(r"race_id(?:=|%3D)(\d{12})", source))
    ids.update(re.findall(r'["\'](\d{12})["\']', source))

    # 対象日と大きく無関係なIDを除外するため先頭4桁=年を最低条件にする。
    year = date_str[:4]
    ids = {x for x in ids if x.startswith(year) and x[4:6] in VENUE_CODE}
    return sorted(ids)


def parse_race_page(source, race_id):
    tokens = visible_tokens(source)
    text = "\n".join(tokens)

    race_no = int(race_id[-2:])

    time_text = ""
    # netkeiba可視テキストによくある 15:35発走 / 発走 15:35
    for pat in (
        r"([0-2]?\d:[0-5]\d)\s*発走",
        r"発走\s*([0-2]?\d:[0-5]\d)",
    ):
        m = re.search(pat, text)
        if m:
            h, mnt = m.group(1).split(":")
            time_text = f"{int(h):02d}:{mnt}"
            break

    race_name = ""
    # title/h1近辺の候補
    for t in tokens[:80]:
        c = clean(t)
        if (
            2 <= len(c) <= 80
            and not re.fullmatch(r"\d+R", c)
            and "netkeiba" not in c.lower()
            and "出馬表" not in c
            and "オッズ" not in c
            and any(k in c for k in ("賞", "ステークス", "カップ", "新馬", "未勝利", "オープン", "クラス", "障害"))
        ):
            race_name = c
            break

    if not race_name:
        race_name = f"{race_no}R"

    rtype, icon = classify(race_name)

    return {
        "race": race_no,
        "time": time_text,
        "name": race_name,
        "conditions": "",
        "race_type": rtype,
        "icon": icon,
        "main": False,
        "race_id": race_id,
    }


def mark_main(races):
    for r in races:
        r["main"] = False
    if not races:
        return races

    graded = [r for r in races if r["race_type"] == "重賞"]
    if graded:
        graded[-1]["main"] = True
        return races

    r11 = [r for r in races if r["race"] == 11]
    if r11:
        r11[-1]["main"] = True
    else:
        races[-1]["main"] = True
    return races


def fetch_netkeiba(date_str):
    url = NETKEIBA_LIST.format(date=date_str)
    print("netkeiba:", url)

    try:
        source = fetch(url)
    except Exception as e:
        print("netkeiba一覧取得失敗:", e)
        return {}

    race_ids = extract_netkeiba_race_ids(source, date_str)
    print("netkeiba race_id候補:", len(race_ids))

    grouped = {}

    for race_id in race_ids:
        venue_code = race_id[4:6]
        venue = VENUE_CODE.get(venue_code)
        if not venue:
            continue

        race_url = (
            "https://race.netkeiba.com/race/shutuba.html"
            f"?race_id={race_id}"
        )
        try:
            page = fetch(race_url, timeout=20)
            race = parse_race_page(page, race_id)
        except Exception as e:
            print("  WARN", venue, race_id, e)
            continue

        if not race["time"]:
            continue

        grouped.setdefault(venue, []).append(race)
        time.sleep(0.15)

    result = {}
    for venue, races in grouped.items():
        # 同一R重複を除去
        unique = {}
        for r in races:
            unique.setdefault(r["race"], r)
        races = sorted(unique.values(), key=lambda x: x["race"])
        races = mark_main(races)

        result[venue] = {
            "source": "netkeiba",
            "channel": CHANNEL_BY_VENUE[venue],
            "tvg_id": TVG_ID[CHANNEL_BY_VENUE[venue]],
            "races": races,
        }
        print(f"  OK {venue}: {len(races)}R")

    return result


def extract_jcom_programs(source, date_str):
    """
    J:COM検索結果から Ch.920 の番組候補を拾う。
    HTMLに日時と番組名が同時に出る場合に抽出。
    """
    tokens = visible_tokens(source)
    target = datetime.datetime.strptime(date_str, "%Y%m%d")
    md = f"{target.month}/{target.day}"

    programs = []

    # 可視テキストを連結して「8/13(木)21:00～21:30」のような塊を探す。
    for i, t in enumerate(tokens):
        c = clean(t)

        # 日付＋時刻が同一トークン
        m = re.search(
            rf"{re.escape(md)}(?:\([^)]*\))?\s*([0-2]?\d):([0-5]\d)\s*[～〜~\-]\s*([0-2]?\d):([0-5]\d)",
            c,
        )

        if not m:
            # 時刻だけの場合、前後に対象日があるか確認
            m = re.search(
                r"([0-2]?\d):([0-5]\d)\s*[～〜~\-]\s*([0-2]?\d):([0-5]\d)",
                c,
            )
            nearby = " ".join(tokens[max(0, i-3):i+2])
            if not m or md not in nearby:
                continue

        start = f"{int(m.group(1)):02d}:{m.group(2)}"
        stop = f"{int(m.group(3)):02d}:{m.group(4)}"

        title = ""
        # 近傍から番組タイトル候補
        for cand in tokens[max(0, i-4):i+5]:
            x = clean(cand)
            if not x or x == c:
                continue
            if "グリーンチャンネルHD" in x:
                continue
            if "録画予約" in x or "見たい" in x:
                continue
            if re.search(r"\d{1,2}/\d{1,2}", x):
                continue
            if re.search(r"\d{1,2}:\d{2}", x):
                continue
            if 2 <= len(x) <= 120:
                title = x
                break

        if title:
            programs.append({"start": start, "stop": stop, "title": title})

    # 重複排除
    uniq = []
    seen = set()
    for p in programs:
        key = (p["start"], p["stop"], p["title"])
        if key not in seen:
            seen.add(key)
            uniq.append(p)

    return uniq


def fetch_jcom_gch(date_str):
    print("J:COM GCH:", JCOM_SEARCH)
    try:
        source = fetch(JCOM_SEARCH)
    except Exception as e:
        return {
            "source": "J:COMテレビ番組表 / グリーンチャンネルHD Ch.920",
            "url": JCOM_SEARCH,
            "ok": False,
            "programs": [],
            "error": str(e),
        }

    programs = extract_jcom_programs(source, date_str)

    return {
        "source": "J:COMテレビ番組表 / グリーンチャンネルHD Ch.920",
        "url": JCOM_SEARCH,
        "ok": bool(programs),
        "programs": programs,
        "error": "" if programs else "対象日の番組行を抽出できませんでした",
    }


def main():
    date_str = datetime.datetime.now(JST).strftime("%Y%m%d")

    venues = fetch_netkeiba(date_str)

    channels = {"east": [], "west": [], "hokkaido": []}
    for venue, info in venues.items():
        channels[info["channel"]].append(venue)

    gch = fetch_jcom_gch(date_str)

    data = {
        "date": date_str,
        "updated_at": datetime.datetime.now(JST).isoformat(),
        "jra_source": "netkeiba",
        "gch_source": "J:COM Ch.920",
        "venues": venues,
        "channels": channels,
        "greenchannel": gch,
    }

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("")
    print("============================")
    print("中央競馬データ取得")
    print("日付:", date_str)
    print("開催場:", ", ".join(venues) if venues else "なし")
    print("EAST:", ", ".join(channels["east"]) or "非開催/未取得")
    print("WEST:", ", ".join(channels["west"]) or "非開催/未取得")
    print("HOKKAIDO:", ", ".join(channels["hokkaido"]) or "非開催/未取得")
    print("J:COM GCH:", f"{len(gch['programs'])}番組" if gch["ok"] else "取得待ち")
    print("JSON:", OUT)
    print("============================")


if __name__ == "__main__":
    main()
