import datetime
import html as html_lib
import json
import re
import urllib.parse
import urllib.request
import http.cookiejar
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

KEIRIN_MAP = {
    "函館": "keirin.hakodate", "青森": "keirin.aomori", "いわき平": "keirin.iwakitaira", "弥彦": "keirin.yahiko",
    "前橋": "keirin.maebashi", "取手": "keirin.toride", "宇都宮": "keirin.utsunomiya", "大宮": "keirin.omiya",
    "西武園": "keirin.seibuen", "京王閣": "keirin.keiogatsu", "立川": "keirin.tachikawa", "松戸": "keirin.matsudo",
    "川崎": "keirin.kawasaki", "平塚": "keirin.hiratsuka", "小田原": "keirin.odawara", "伊東": "keirin.ito",
    "静岡": "keirin.shizuoka", "名古屋": "keirin.nagoya", "岐阜": "keirin.gifu", "大垣": "keirin.ogaki",
    "豊橋": "keirin.toyohashi", "松阪": "keirin.matsusaka", "四日市": "keirin.yokkaichi", "富山": "keirin.toyama",
    "福井": "keirin.fukui", "奈良": "keirin.nara", "岸和田": "keirin.kishiwada", "和歌山": "keirin.wakayama",
    "玉野": "keirin.tamano", "広島": "keirin.hiroshima", "防府": "keirin.hofu", "小松島": "keirin.komatsushima",
    "松山": "keirin.matsuyama", "高知": "keirin.kochi", "高松": "keirin.takamatsu", "向日町": "keirin.mukomachi",
    "小倉": "keirin.kokura", "久留米": "keirin.kurume", "武雄": "keirin.takeo", "佐世保": "keirin.sasebo",
    "別府": "keirin.beppu", "熊本": "keirin.kumamoto", "千葉": "keirin.pist6"
}
KEIBA_MAP = {
    "帯広": "chihou.obihiro", "門別": "chihou.mombetsu", "盛岡": "chihou.morioka", "水沢": "chihou.mizusawa",
    "浦和": "chihou.urawa", "船橋": "chihou.funabashi", "大井": "chihou.oi", "川崎": "chihou.kawasaki_keiba",
    "金沢": "chihou.kanazawa", "名古屋": "chihou.nagoya_keiba", "笠松": "chihou.kasamatsu", "園田": "chihou.sonoda",
    "姫路": "chihou.himeji", "高知": "chihou.kochi_keiba", "佐賀": "chihou.saga",
}

JRA_STREAM_MAP = {
    "JRA EAST": "jra.east",
    "JRA WEST": "jra.west",
    "JRA HOKKAIDO": "jra.hokkaido",
}

JRA_VENUE_TO_STREAM = {
    "東京": "JRA EAST", "中山": "JRA EAST", "新潟": "JRA EAST", "福島": "JRA EAST",
    "京都": "JRA WEST", "阪神": "JRA WEST", "中京": "JRA WEST", "小倉": "JRA WEST",
    "札幌": "JRA HOKKAIDO", "函館": "JRA HOKKAIDO",
}

AUTO_MAP = {"川口": "auto.kawaguchi", "伊勢崎": "auto.isesaki", "浜松": "auto.hamamatsu", "飯塚": "auto.iizuka", "山陽": "auto.sanyo"}


NAR_VENUE_CODES = {
    "帯広": "03", "盛岡": "10", "水沢": "11", "浦和": "18", "船橋": "19",
    "大井": "20", "川崎": "21", "金沢": "22", "笠松": "23", "名古屋": "24",
    "園田": "27", "姫路": "28", "高知": "31", "佐賀": "32", "門別": "36",
}

NAR_RACE_LIST_URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList"
    "?k_babaCode={code}&k_raceDate={date}"
)



BOAT_MAP = {
    "01 桐生": "boat.kiryu",
    "02 戸田": "boat.toda",
    "03 江戸川": "boat.edogawa",
    "04 平和島": "boat.heiwajima",
    "05 多摩川": "boat.tamagawa",
    "06 浜名湖": "boat.hamanako",
    "07 蒲郡": "boat.gamagori",
    "08 常滑": "boat.tokoname",
    "09 津": "boat.tsu",
    "10 三国": "boat.mikuni",
    "11 びわこ": "boat.biwako",
    "12 住之江": "boat.suminoe",
    "13 尼崎": "boat.amagasaki",
    "14 鳴門": "boat.naruto",
    "15 丸亀": "boat.marugame",
    "16 児島": "boat.kojima",
    "17 宮島": "boat.miyajima",
    "18 徳山": "boat.tokuyama",
    "19 下関": "boat.shimonoseki",
    "20 若松": "boat.wakamatsu",
    "21 芦屋": "boat.ashiya",
    "22 福岡": "boat.fukuoka",
    "23 唐津": "boat.karatsu",
    "24 大村": "boat.omura",
}

BOAT_TODAY_URL = (
    "https://raw.githubusercontent.com/"
    "earphone1981/ganble/main/boatrace_today.json"
)


BOAT_OFFICIAL_INDEX_URL = (
    "https://www.boatrace.jp/owpc/pc/race/index?hd={date}"
)

BOAT_OFFICIAL_RACEINDEX_URL = (
    "https://www.boatrace.jp/owpc/pc/race/raceindex?hd={date}&jcd={code}"
)

BOAT_CODE_BY_NAME = {
    "01 桐生": "01",
    "02 戸田": "02",
    "03 江戸川": "03",
    "04 平和島": "04",
    "05 多摩川": "05",
    "06 浜名湖": "06",
    "07 蒲郡": "07",
    "08 常滑": "08",
    "09 津": "09",
    "10 三国": "10",
    "11 びわこ": "11",
    "12 住之江": "12",
    "13 尼崎": "13",
    "14 鳴門": "14",
    "15 丸亀": "15",
    "16 児島": "16",
    "17 宮島": "17",
    "18 徳山": "18",
    "19 下関": "19",
    "20 若松": "20",
    "21 芦屋": "21",
    "22 福岡": "22",
    "23 唐津": "23",
    "24 大村": "24",
}

BOAT_NAME_BY_CODE = {code: name for name, code in BOAT_CODE_BY_NAME.items()}

# EPG generation window.
# Always generate today + tomorrow + the day after tomorrow.
EPG_DAYS = 3

ICON_MAP = {
    "keirin": "🚲",
    "keiba": "🏇",
    "auto": "🏍️",
    "boat": "🚤",
}

BOAT_TODAY_URL = (
    "https://raw.githubusercontent.com/"
    "earphone1981/ganble/main/boatrace_today.json"
)

KEIBA_SCHEDULE_URL = (
    "https://raw.githubusercontent.com/"
    "earphone1981/ganble/main/keiba_schedule.json"
)


KEIRIN_SCHEDULE_URL = (
    "https://raw.githubusercontent.com/"
    "earphone1981/ganble/main/keirin_schedule.json"
)

AUTORACE_SCHEDULE_URL = (
    "https://raw.githubusercontent.com/"
    "earphone1981/ganble/main/autorace_schedule.json"
)


GCH_GUIDES_URL = (
    "https://github.com/karenda-jp/etc/raw/refs/heads/main/guides.xml"
)
GCH_TVG_ID = "jra.gch"
GCH_DISPLAY_NAME = "グリーンチャンネル"


def format_time_xml(dt):
    return dt.strftime("%Y%m%d%H%M%S +0900")


def fetch_json(url, label):
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            text = response.read().decode("utf-8-sig")
        data = json.loads(text)
        print(f"{label}: 取得成功")
        return data
    except Exception as e:
        print(f"{label}: 取得失敗: {e}")
        return {}


def load_boatrace_today():
    return fetch_json(BOAT_TODAY_URL, "BOAT JSON")


def load_keiba_schedule():
    return fetch_json(KEIBA_SCHEDULE_URL, "KEIBA JSON")


def load_keirin_schedule():
    return fetch_json(KEIRIN_SCHEDULE_URL, "KEIRIN JSON")


def load_autorace_schedule():
    return fetch_json(AUTORACE_SCHEDULE_URL, "AUTORACE JSON")


def add_programme(tv, channel, start_dt, stop_dt, title, desc=""):
    if stop_dt <= start_dt:
        return None

    prog = ET.SubElement(
        tv,
        "programme",
        start=format_time_xml(start_dt),
        stop=format_time_xml(stop_dt),
        channel=channel,
    )
    ET.SubElement(prog, "title", lang="ja").text = title

    if desc:
        ET.SubElement(prog, "desc", lang="ja").text = desc

    return prog


def day_emoji(day_type):
    return {
        "モーニング": "🌅",
        "通常": "☀️",
        "デイ": "☀️",
        "薄暮": "🌇",
        "サマータイム": "🌇",
        "ナイター": "🌙",
        "ミッドナイト": "⭐",
    }.get(day_type, "☀️")


def build_manual_category(
    tv,
    date_str,
    category,
    target_map,
    cat_data,
    JST,
    today_display,
):
    cat_label = {
        "keirin": "競輪",
        "keiba": "競馬",
        "auto": "オートレース",
    }.get(category, "")

    for v_name, tvg_id in target_map.items():
        day_start = datetime.datetime.strptime(
            f"{date_str} 01:00", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        day_end = datetime.datetime.strptime(
            f"{date_str} 23:59", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        if v_name not in cat_data:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"💤 本日非開催 {v_name}（{cat_label}）",
                f"本日は{v_name}での開催予定はありません。",
            )
            continue

        info = cat_data[v_name]
        is_girls = info.get("is_girls", False)
        day_type = info.get("day_type", "デイ")
        emoji = day_emoji(day_type)
        girls_tag = "💛ガールズ" if is_girls else ""

        grade_list = [
            "JpnIII", "JpnII", "JpnI",
            "GIII", "GII", "GI",
            "FII", "FI", "SG",
        ]
        grade_found = next(
            (g for g in grade_list if g in info["desc"]),
            "",
        )

        day_match_str = ""
        for term in [
            "初日", "2日目", "3日目", "4日目",
            "5日目", "決勝戦", "最終日",
        ]:
            if term in info["desc"]:
                day_match_str = term
                break

        match_text = (
            "🏆 決勝戦"
            if "決勝戦" in info["desc"]
            else day_match_str
        )

        grade_prefix = f"【{grade_found}】" if grade_found else ""

        title_parts = [
            grade_prefix,
            "🔴 LIVE",
            v_name,
            f"{emoji}{day_type}",
            match_text,
            girls_tag,
            f"（{cat_label}）",
        ]
        title_live = " ".join(p for p in title_parts if p)

        start_dt = datetime.datetime.strptime(
            f"{date_str} {info['start']}", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        end_dt = datetime.datetime.strptime(
            f"{date_str} {info['end']}", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        if end_dt <= start_dt:
            end_dt += datetime.timedelta(days=1)

        pre_start = start_dt - datetime.timedelta(minutes=10)
        post_end = end_dt + datetime.timedelta(minutes=10)

        desc_text = (
            f"{ICON_MAP.get(category, '⭐')} 開催地: {v_name} ({day_type})\n"
            f"🏆 グレード: {grade_found if grade_found else '通常開催'}\n"
            f"✨ ガールズ: {'あり 💛' if is_girls else 'なし'}\n"
            f"📢 内容: {info['desc']}\n"
            f"⏰ 時間: {info['start']} - {info['end']}\n"
            f"📅 日付: {today_display}"
        )

        if day_start < pre_start:
            add_programme(
                tv,
                tvg_id,
                day_start,
                pre_start,
                f"⏳ 待機 {v_name} ({emoji}{day_type} "
                f"1R {info['start']}開始)（{cat_label}）",
                desc_text,
            )

        add_programme(
            tv,
            tvg_id,
            max(pre_start, day_start),
            post_end,
            title_live,
            desc_text,
        )

        if post_end < day_end:
            add_programme(
                tv,
                tvg_id,
                post_end,
                day_end,
                f"🏁 終了 {v_name} ({emoji}{day_type})（{cat_label}）",
                f"{v_name} ({day_type}) の放送は終了しました。",
            )



def infer_local_keiba_day_type(races):
    if not races:
        return "デイ"
    try:
        first_hour = int(races[0].get("time", "12:00").split(":")[0])
        last_hour = int(races[-1].get("time", "17:00").split(":")[0])
    except Exception:
        return "デイ"
    if first_hour < 10:
        return "モーニング"
    if last_hour >= 19 or first_hour >= 14:
        return "ナイター"
    if last_hour >= 17:
        return "薄暮"
    return "デイ"


def fetch_nar_future_schedule(date_str):
    """NAR公式の指定日出馬表から地方競馬の各R時刻・名称を取得する。"""
    date_param = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:8]}"
    encoded_date = urllib.parse.quote(date_param, safe="")
    local = {}

    for venue, code in NAR_VENUE_CODES.items():
        url = NAR_RACE_LIST_URL.format(code=code, date=encoded_date)
        source = fetch_text(url, f"NAR {date_str} {venue}")
        if not source:
            continue

        plain = strip_html_tags(source)
        if venue not in plain or "当日メニュー" not in plain:
            continue

        row_re = re.compile(
            r"\b(\d{1,2})R\b\s+([0-2]?\d:[0-5]\d)\s+(.*?)"
            r"(?=\s+\d{1,2}R\s+[0-2]?\d:[0-5]\d|\s+重賞競走優勝馬検索|\Z)",
            flags=re.S,
        )
        races_by_no = {}
        for m in row_re.finditer(plain):
            race_no = int(m.group(1))
            if not 1 <= race_no <= 12:
                continue
            hhmm = m.group(2)
            if len(hhmm) == 4:
                hhmm = "0" + hhmm
            tail = re.sub(r"\s+", " ", m.group(3)).strip()
            name = re.split(
                r"\s+(?:右|左|直線)\d+m|\s+オッズ\b|\s+映像\b|\s+成績\b",
                tail,
                maxsplit=1,
            )[0].strip()[:160]
            races_by_no[race_no] = {
                "race": str(race_no),
                "time": hhmm,
                "name": name or "競走",
                "race_type": "一般",
                "icon": "🐎",
                "main": race_no == 12,
            }

        races = [races_by_no[n] for n in sorted(races_by_no)]
        if not races:
            continue

        local[venue] = {
            "day_type": infer_local_keiba_day_type(races),
            "races": races,
            "source": "NAR公式",
        }

    return {
        "date": date_str,
        "updated_at": datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat(),
        "jra": {},
        "local": local,
    }


def fetch_nar_epg_days(today_date, days):
    out = {}
    for offset in range(1, days):
        d = today_date + datetime.timedelta(days=offset)
        date_str = d.strftime("%Y%m%d")
        print(f"NAR未来日: {date_str} ...", end="", flush=True)
        data = fetch_nar_future_schedule(date_str)
        out[date_str] = data
        print(f" {len(data.get('local', {}))}場")
    return out


def build_keiba_race_epg(
    tv,
    date_str,
    keiba_data,
    JST,
    today_display,
):
    """
    keiba_schedule.json の各Rを1番組としてEPG化。
    その日のJSONが無い場合は False を返して手入力へフォールバック。
    """
    if not keiba_data:
        return False

    if keiba_data.get("date") != date_str:
        return False

    merged = {}

    for category_key in ("jra", "local"):
        for venue, info in keiba_data.get(category_key, {}).items():
            merged[venue] = {
                **info,
                "_category": category_key,
            }

    if not merged:
        return False

    handled = set()

    for venue, info in merged.items():
        tvg_id = KEIBA_MAP.get(venue)
        if not tvg_id:
            print(f"KEIBA: tvg-id未登録: {venue}")
            continue

        races = info.get("races", [])
        if not races:
            continue

        handled.add(venue)

        day_type = info.get("day_type", "デイ")
        emoji = day_emoji(day_type)
        category_name = "JRA" if info.get("_category") == "jra" else "地方競馬"

        day_start = datetime.datetime.strptime(
            f"{date_str} 01:00", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        day_end = datetime.datetime.strptime(
            f"{date_str} 23:59", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        race_times = []
        for race in races:
            time_text = race.get("time", "")
            try:
                dt = datetime.datetime.strptime(
                    f"{date_str} {time_text}", "%Y%m%d %H:%M"
                ).replace(tzinfo=JST)
            except Exception:
                continue
            race_times.append((race, dt))

        if not race_times:
            continue

        first_race_dt = race_times[0][1]
        pre_start = max(
            day_start,
            first_race_dt - datetime.timedelta(minutes=20),
        )

        if day_start < pre_start:
            add_programme(
                tv,
                tvg_id,
                day_start,
                pre_start,
                f"⏳ 待機 {venue} {emoji}{day_type}",
                f"{category_name} {venue}\n"
                f"1R発走予定 {race_times[0][0].get('time', '')}\n"
                f"📅 {today_display}",
            )

        # 各Rを「発走10分前～次R発走10分前」で連続表示
        for idx, (race, start_time) in enumerate(race_times):
            block_start = max(
                pre_start,
                start_time - datetime.timedelta(minutes=10),
            )

            if idx + 1 < len(race_times):
                next_time = race_times[idx + 1][1]
                block_stop = next_time - datetime.timedelta(minutes=10)
            else:
                block_stop = start_time + datetime.timedelta(minutes=30)

            if block_stop <= block_start:
                block_stop = start_time + datetime.timedelta(minutes=15)

            race_no = race.get("race", "")
            race_name = race.get("name", "").strip()
            race_type = race.get("race_type", "一般")
            icon = race.get("icon", "🐎")
            main = bool(race.get("main"))
            conditions = race.get("conditions", "").strip()

            main_mark = "🏆 MAIN " if main else ""
            display_name = race_name if race_name else race_type

            # Visible EPG title:
            # venue / R / start / official race title / class or conditions.
            title_parts = [
                f"{main_mark}{icon}".strip(),
                venue,
                f"{race_no}R",
                f"{race.get('time', '')}発走",
                display_name,
            ]

            if race_type and race_type not in {"一般", display_name}:
                title_parts.append(f"【{race_type}】")

            if (
                conditions
                and conditions != race_name
                and conditions != race_type
                and conditions not in display_name
            ):
                title_parts.append(conditions)

            title = " ".join(x for x in title_parts if x).strip()

            desc_lines = [
                f"{category_name} {venue}",
                f"{emoji} 開催区分: {day_type}",
                f"⏰ 発走予定: {race.get('time', '')}",
                f"🏷️ 種別: {race_type}",
            ]

            if race_name:
                desc_lines.append(f"📢 レース名: {race_name}")

            if conditions and conditions != race_name:
                desc_lines.append(f"📋 条件: {conditions}")

            if main:
                desc_lines.append("🏆 メインレース")

            desc_lines.append(f"📅 {today_display}")

            add_programme(
                tv,
                tvg_id,
                block_start,
                min(block_stop, day_end),
                title,
                "\n".join(desc_lines),
            )

        finish_start = race_times[-1][1] + datetime.timedelta(minutes=30)

        if finish_start < day_end:
            add_programme(
                tv,
                tvg_id,
                finish_start,
                day_end,
                f"🏁 終了 {venue} {emoji}{day_type}",
                f"{venue}の本日の競馬は終了しました。",
            )

    # JSONに無い地方競馬チャンネルは非開催表示。
    # JRA系は別処理、GCHは guides.xml から取得するためここでは除外。
    for venue, tvg_id in KEIBA_MAP.items():
        if venue in {"ＪＲＡ公式", "ＪＲＡグリーン"}:
            continue
        if venue in handled:
            continue

        day_start = datetime.datetime.strptime(
            f"{date_str} 01:00", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        day_end = datetime.datetime.strptime(
            f"{date_str} 23:59", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        add_programme(
            tv,
            tvg_id,
            day_start,
            day_end,
            f"💤 本日非開催 {venue}（競馬）",
            f"本日は{venue}のレース情報を取得していません。",
        )

    print(f"KEIBA EPG: {len(handled)}場を各R単位で生成")
    return True



def build_keirin_race_epg(
    tv,
    date_str,
    keirin_data,
    JST,
    today_display,
):
    if not keirin_data or keirin_data.get("date") != date_str:
        return False

    venues = keirin_data.get("venues", {})
    if not venues:
        return False

    handled = set()

    for venue, info in venues.items():
        tvg_id = KEIRIN_MAP.get(venue) or info.get("tvg_id", "")
        if not tvg_id:
            print(f"KEIRIN: tvg-id未登録: {venue}")
            continue

        races = info.get("races", [])
        if not races:
            continue

        race_times = []
        for race in races:
            try:
                dt = datetime.datetime.strptime(
                    f"{date_str} {race.get('time','')}",
                    "%Y%m%d %H:%M",
                ).replace(tzinfo=JST)
            except Exception:
                continue
            race_times.append((race, dt))

        if not race_times:
            continue

        handled.add(venue)

        day_type = info.get("day_type", "デイ")
        day_icon = info.get("day_emoji", day_emoji(day_type))
        grade = info.get("grade", "")
        event_name = clean_epg_meta_text(info.get("event_name", ""))
        event_day = clean_epg_meta_text(info.get("event_day", ""))

        day_start = datetime.datetime.strptime(
            f"{date_str} 01:00", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)
        day_end = datetime.datetime.strptime(
            f"{date_str} 23:59", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        pre_start = max(
            day_start,
            race_times[0][1] - datetime.timedelta(minutes=20),
        )

        if day_start < pre_start:
            add_programme(
                tv, tvg_id, day_start, pre_start,
                f"⏳ 待機 {venue} {day_icon}{day_type}",
                "\n".join(
                    x for x in [
                        f"🚲 競輪 {venue}",
                        f"{grade} {event_name}".strip(),
                        event_day,
                        f"1R発走予定 {race_times[0][0].get('time','')}",
                        f"📅 {today_display}",
                    ] if x
                ),
            )

        for idx, (race, start_time) in enumerate(race_times):
            block_start = max(
                pre_start,
                start_time - datetime.timedelta(minutes=8),
            )

            if idx + 1 < len(race_times):
                next_time = race_times[idx + 1][1]
                block_stop = next_time - datetime.timedelta(minutes=8)
            else:
                block_stop = start_time + datetime.timedelta(minutes=25)

            if block_stop <= block_start:
                block_stop = start_time + datetime.timedelta(minutes=12)

            race_name = race.get("name", "").strip() or "競走"
            race_no = race.get("race", "")
            main = bool(race.get("main"))
            girls = bool(race.get("girls"))

            title_parts = []
            if main:
                title_parts.append("🏆 MAIN")
            if girls:
                title_parts.append("💛")
            else:
                title_parts.append("🚲")
            if grade and main:
                title_parts.append(f"【{grade}】")
            title_parts.append(f"{venue} {race_no}R")
            title_parts.append(f"{race.get('time', '')}発走")
            # Keep the exact source race name, e.g. A級予選 / 一次予選 / 準決勝 / 決勝.
            title_parts.append(race_name)

            race_class = race.get("race_class", "").strip()
            if race_class and race_class not in race_name:
                title_parts.append(f"【{race_class}】")

            desc_lines = [
                f"🚲 競輪 {venue}",
                f"{day_icon} 開催区分: {day_type}",
                f"⏰ 発走予定: {race.get('time','')}",
                f"🏷️ {race.get('race_class','競輪')}",
            ]
            if grade:
                desc_lines.append(f"🏆 グレード: {grade}")
            if event_name:
                desc_lines.append(f"📢 開催名: {event_name}")
            if event_day:
                desc_lines.append(f"📅 開催日次: {event_day}")
            if girls:
                desc_lines.append("💛 ガールズ")
            is_semi = bool(race.get("is_semi")) or "準決" in race_name
            is_final = bool(race.get("is_final")) and not is_semi

            if is_semi:
                desc_lines.append("🔥 準決勝")
            if is_final:
                desc_lines.append("🏆 決勝")
            if main:
                desc_lines.append("🏆 メインレース")

            add_programme(
                tv,
                tvg_id,
                block_start,
                min(block_stop, day_end),
                " ".join(x for x in title_parts if x),
                "\n".join(desc_lines),
            )

        finish = race_times[-1][1] + datetime.timedelta(minutes=25)
        if finish < day_end:
            add_programme(
                tv, tvg_id, finish, day_end,
                f"🏁 終了 {venue} {day_icon}{day_type}",
                f"{venue}の本日の競輪は終了しました。",
            )

    print(f"KEIRIN EPG: {len(handled)}場を各R単位で生成")
    return True


def clean_epg_meta_text(value):
    """Drop broken metadata such as a lone Japanese parenthesis from EPG."""
    s = re.sub(r"\s+", " ", str(value or "")).strip()
    if not s:
        return ""
    s = s.strip(" \t\r\n-|｜()（）[]【】『』「」・:：,，.。")
    if not s:
        return ""
    if not re.search(r"[0-9A-Za-zぁ-んァ-ヶ一-龠々〆ヶ]", s):
        return ""
    return s


def build_autorace_race_epg(
    tv,
    date_str,
    autorace_data,
    JST,
    today_display,
):
    if not autorace_data or autorace_data.get("date") != date_str:
        return False

    venues = autorace_data.get("venues", {})
    if not venues:
        return False

    handled = set()

    for venue, info in venues.items():
        tvg_id = AUTO_MAP.get(venue) or info.get("tvg_id", "")
        if not tvg_id:
            print(f"AUTORACE: tvg-id未登録: {venue}")
            continue

        races = info.get("races", [])
        if not races:
            continue

        race_times = []
        for race in races:
            try:
                dt = datetime.datetime.strptime(
                    f"{date_str} {race.get('time','')}",
                    "%Y%m%d %H:%M",
                ).replace(tzinfo=JST)
            except Exception:
                continue
            race_times.append((race, dt))

        if not race_times:
            continue

        handled.add(venue)

        day_type = info.get("day_type", "デイ")
        day_icon = info.get("day_emoji", day_emoji(day_type))
        grade = info.get("grade", "")
        event_name = info.get("event_name", "")
        event_day = info.get("event_day", "")

        day_start = datetime.datetime.strptime(
            f"{date_str} 01:00", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)
        day_end = datetime.datetime.strptime(
            f"{date_str} 23:59", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        pre_start = max(
            day_start,
            race_times[0][1] - datetime.timedelta(minutes=20),
        )

        if day_start < pre_start:
            add_programme(
                tv, tvg_id, day_start, pre_start,
                f"⏳ 待機 {venue} {day_icon}{day_type}",
                "\n".join(
                    x for x in [
                        f"🏍️ オートレース {venue}",
                        f"{grade} {event_name}".strip(),
                        event_day,
                        f"1R発走予定 {race_times[0][0].get('time','')}",
                        f"📅 {today_display}",
                    ] if x
                ),
            )

        for idx, (race, start_time) in enumerate(race_times):
            block_start = max(
                pre_start,
                start_time - datetime.timedelta(minutes=8),
            )

            if idx + 1 < len(race_times):
                next_time = race_times[idx + 1][1]
                block_stop = next_time - datetime.timedelta(minutes=8)
            else:
                block_stop = start_time + datetime.timedelta(minutes=25)

            if block_stop <= block_start:
                block_stop = start_time + datetime.timedelta(minutes=12)

            race_no = race.get("race", "")
            race_name = race.get("name", "").strip() or race.get("race_type", "競走")
            raw_main = bool(race.get("main"))
            is_semi = bool(race.get("is_semi")) or "準決" in race_name
            is_final = (
                bool(race.get("is_final"))
                or "優勝" in race_name
                or "決勝" in race_name
            ) and not is_semi
            is_special_main = any(
                word in race_name
                for word in ("特選", "特別選抜", "選抜戦")
            )
            main = raw_main and (is_final or is_special_main)
            icon = race.get("icon", "🏍️")

            title_parts = []
            if main:
                title_parts.append("🏆 MAIN")
            title_parts.append(icon)
            if grade and main:
                title_parts.append(f"【{grade}】")
            title_parts.append(f"{venue} {race_no}R")
            title_parts.append(f"{race.get('time', '')}発走")
            # Keep the exact source race title/stage, e.g. 一次予選 / 準決勝 / 優勝戦.
            title_parts.append(race_name)

            race_type = race.get("race_type", "").strip()
            if race_type and race_type not in race_name:
                title_parts.append(f"【{race_type}】")

            desc_lines = [
                f"🏍️ オートレース {venue}",
                f"{day_icon} 開催区分: {day_type}",
                f"⏰ 発走予定: {race.get('time','')}",
                f"🏷️ 種別: {race.get('race_type','')}",
            ]
            if grade:
                desc_lines.append(f"🏆 グレード: {grade}")
            if event_name:
                desc_lines.append(f"📢 開催名: {event_name}")
            if event_day:
                desc_lines.append(f"📅 開催日次: {event_day}")
            if is_semi:
                desc_lines.append("🔥 準決勝")
            if is_final:
                desc_lines.append("🏆 優勝戦")
            if main:
                desc_lines.append("🏆 メインレース")

            add_programme(
                tv,
                tvg_id,
                block_start,
                min(block_stop, day_end),
                " ".join(x for x in title_parts if x),
                "\n".join(desc_lines),
            )

        finish = race_times[-1][1] + datetime.timedelta(minutes=25)
        if finish < day_end:
            add_programme(
                tv, tvg_id, finish, day_end,
                f"🏁 終了 {venue} {day_icon}{day_type}",
                f"{venue}の本日のオートレースは終了しました。",
            )

    print(f"AUTORACE EPG: {len(handled)}場を各R単位で生成")
    return True


def parse_xmltv_datetime(value, default_tz):
    """XMLTV start/stop (YYYYMMDDHHMMSS +0900 等)をtimezone付きdatetimeへ変換。"""
    s = str(value or "").strip()
    m = re.match(r"^(\d{8,14})\s*([+-]\d{4})?", s)
    if not m:
        return None

    digits = m.group(1)
    offset = m.group(2)

    if len(digits) == 8:
        digits += "000000"
    elif len(digits) == 10:
        digits += "0000"
    elif len(digits) == 12:
        digits += "00"
    elif len(digits) != 14:
        return None

    try:
        if offset:
            return datetime.datetime.strptime(
                f"{digits} {offset}",
                "%Y%m%d%H%M%S %z",
            )
        return datetime.datetime.strptime(
            digits,
            "%Y%m%d%H%M%S",
        ).replace(tzinfo=default_tz)
    except Exception:
        return None


def normalize_channel_name(value):
    return re.sub(r"[\s　]+", "", str(value or "")).strip()


def import_gch_from_guides(tv, today_date, days, JST):
    """
    karenda-jp guides.xml からグリーンチャンネルだけを抽出し、
    channel id を jra.gch に統一して本番EPGへ追加する。
    """
    try:
        req = urllib.request.Request(
            GCH_GUIDES_URL,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
        source_root = ET.fromstring(raw)
    except Exception as e:
        print(f"GCH guides.xml: 取得失敗: {e}")
        return 0

    exact_ids = []
    fallback_ids = []
    target_norm = normalize_channel_name(GCH_DISPLAY_NAME)

    for ch in source_root.findall("channel"):
        ch_id = ch.get("id", "")
        names = [
            normalize_channel_name(x.text)
            for x in ch.findall("display-name")
            if x.text
        ]
        if target_norm in names:
            exact_ids.append(ch_id)
        elif any(target_norm in name for name in names):
            fallback_ids.append(ch_id)

    source_ids = exact_ids or fallback_ids
    source_ids = [x for x in source_ids if x]

    if not source_ids:
        print("GCH guides.xml: グリーンチャンネルのchannel idを発見できません")
        return 0

    window_start = datetime.datetime.combine(
        today_date,
        datetime.time.min,
        tzinfo=JST,
    )
    window_end = window_start + datetime.timedelta(days=days)

    imported = 0
    for prog in source_root.findall("programme"):
        if prog.get("channel", "") not in source_ids:
            continue

        start_dt = parse_xmltv_datetime(prog.get("start"), JST)
        stop_dt = parse_xmltv_datetime(prog.get("stop"), JST)
        if not start_dt:
            continue

        start_jst = start_dt.astimezone(JST)
        stop_jst = stop_dt.astimezone(JST) if stop_dt else start_jst + datetime.timedelta(hours=1)

        # 今日0:00～3日後0:00と重なる番組だけ採用。
        if stop_jst <= window_start or start_jst >= window_end:
            continue

        copied = ET.fromstring(ET.tostring(prog, encoding="utf-8"))
        copied.set("channel", GCH_TVG_ID)
        tv.append(copied)
        imported += 1

    print(
        f"GCH guides.xml: source={','.join(source_ids)} / "
        f"{imported}番組を{GCH_TVG_ID}へ統合"
    )
    return imported


def fetch_text(url, label="URL"):
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
                "Accept-Language": "ja-JP,ja;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"{label}: 取得失敗: {e}")
        return ""


def strip_html_tags(source):
    if not source:
        return ""
    source = re.sub(r"(?is)<script.*?</script>", " ", source)
    source = re.sub(r"(?is)<style.*?</style>", " ", source)
    source = re.sub(r"(?s)<[^>]+>", " ", source)
    source = html_lib.unescape(source)
    source = re.sub(r"\s+", " ", source)
    return source.strip()


def extract_boat_active_codes(index_html):
    # Official daily index links contain jcd=01 ... jcd=24.
    found = set(
        re.findall(r"(?:[?&]|&amp;)jcd=(\d{2})", index_html or "")
    )
    return sorted(code for code in found if code in BOAT_NAME_BY_CODE)


def extract_boat_race_times(race_html):
    """Return [(race_no, HH:MM), ...] from official raceindex HTML."""
    if not race_html:
        return []

    compact = re.sub(r"\s+", " ", html_lib.unescape(race_html))
    found = {}

    # Works with both visible table text and link-heavy HTML:
    # 1R ... 15:28, 2R ... 16:02, ...
    for race_no in range(1, 13):
        patterns = [
            rf">\s*{race_no}R\s*<.*?([0-2]?\d:[0-5]\d)",
            rf"\b{race_no}R\b.{{0,1200}}?([0-2]?\d:[0-5]\d)",
        ]
        for pat in patterns:
            m = re.search(pat, compact, flags=re.I | re.S)
            if m:
                found[race_no] = m.group(1)
                break

    # Fallback on stripped text.
    if len(found) < 2:
        plain = strip_html_tags(race_html)
        for race_no in range(1, 13):
            if race_no in found:
                continue
            m = re.search(
                rf"\b{race_no}R\b.{{0,150}}?([0-2]?\d:[0-5]\d)",
                plain,
                flags=re.I,
            )
            if m:
                found[race_no] = m.group(1)

    return [(n, found[n]) for n in sorted(found)]


def infer_boat_day_type(race_times):
    if not race_times:
        return "開催", "🚤"

    first = race_times[0][1]
    try:
        hour = int(first.split(":")[0])
    except Exception:
        return "開催", "🚤"

    if hour < 10:
        return "モーニング", "🌅"
    if hour >= 14:
        return "ナイター", "🌙"
    return "デイ", "☀️"


def fetch_boat_week_schedule(today_date, days):
    """
    Official BOAT RACE pages:
      index?hd=YYYYMMDD -> active venues for that date
      raceindex?hd=YYYYMMDD&jcd=XX -> 1R..12R race times
    """
    week = {}

    for offset in range(days):
        d = today_date + datetime.timedelta(days=offset)
        date_str = d.strftime("%Y%m%d")
        print(f"BOAT 週間予定: {date_str} ...", end="", flush=True)

        index_url = BOAT_OFFICIAL_INDEX_URL.format(date=date_str)
        index_html = fetch_text(index_url, f"BOAT index {date_str}")

        if not index_html:
            week[date_str] = {
                "ok": False,
                "venues": {},
            }
            print(" 取得失敗")
            continue

        active_codes = extract_boat_active_codes(index_html)
        venues = {}

        for code in active_codes:
            v_name = BOAT_NAME_BY_CODE.get(code)
            if not v_name:
                continue

            race_url = BOAT_OFFICIAL_RACEINDEX_URL.format(
                date=date_str,
                code=code,
            )
            race_html = fetch_text(race_url, f"BOAT {date_str} {code}")
            race_times = extract_boat_race_times(race_html)
            day_type, emoji = infer_boat_day_type(race_times)

            # Race title = first H2-like heading from the race page when available.
            title = ""
            if race_html:
                m = re.search(r"(?is)<h2[^>]*>(.*?)</h2>", race_html)
                if m:
                    title = strip_html_tags(m.group(1))

            venues[v_name] = {
                "code": code,
                "title": title,
                "day_type": day_type,
                "emoji": emoji,
                "races": [
                    {"race": str(race_no), "time": hhmm}
                    for race_no, hhmm in race_times
                ],
            }

        week[date_str] = {
            "ok": True,
            "venues": venues,
        }
        print(f" {len(venues)}場")

    return week


def build_boat_race_epg(
    tv,
    date_str,
    boat_week,
    JST,
    today_display,
):
    """
    Build BOAT EPG for one date from official schedule.
    Returns True if the daily official index was available.
    """
    day_info = boat_week.get(date_str, {})
    if not day_info.get("ok"):
        return False

    venues = day_info.get("venues", {})

    for v_name, tvg_id in BOAT_MAP.items():
        day_start = datetime.datetime.strptime(
            f"{date_str} 01:00", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)
        day_end = datetime.datetime.strptime(
            f"{date_str} 23:59", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        info = venues.get(v_name)
        if not info:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"💤 本日非開催 {v_name}（ボートレース）",
                f"BOAT RACE公式の{today_display}開催一覧に"
                f"{v_name}は掲載されていません。",
            )
            continue

        races = info.get("races", [])
        day_type = info.get("day_type", "開催")
        emoji = info.get("emoji", "🚤")
        event_title = info.get("title", "")

        # Future cards can exist before individual race times are published.
        if not races:
            title = f"📅 開催予定 {v_name} {emoji}{day_type} 🚤ボートレース"
            desc_lines = [
                f"🚤 ボートレース {v_name}",
                f"{emoji} 開催区分: {day_type}",
                f"📅 {today_display}",
                "BOAT RACE公式の開催一覧で開催を確認済み。",
                "1R～12Rの発走予定時刻は公開後に自動反映します。",
            ]
            if event_title:
                desc_lines.insert(1, f"📢 {event_title}")
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                title,
                "\n".join(desc_lines),
            )
            continue

        race_dts = []
        for race in races:
            try:
                dt = datetime.datetime.strptime(
                    f"{date_str} {race.get('time','')}",
                    "%Y%m%d %H:%M",
                ).replace(tzinfo=JST)
            except Exception:
                continue
            race_dts.append((race, dt))

        if not race_dts:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"📅 開催予定 {v_name} {emoji}{day_type} 🚤ボートレース",
                f"🚤 ボートレース {v_name}\n📅 {today_display}",
            )
            continue

        pre_start = max(
            day_start,
            race_dts[0][1] - datetime.timedelta(minutes=20),
        )

        if day_start < pre_start:
            add_programme(
                tv,
                tvg_id,
                day_start,
                pre_start,
                f"⏳ 待機 {v_name} {emoji}{day_type}",
                "\n".join(
                    x for x in [
                        f"🚤 ボートレース {v_name}",
                        f"📢 {event_title}" if event_title else "",
                        f"1R {race_dts[0][0].get('time','')} 発走予定",
                        f"📅 {today_display}",
                    ] if x
                ),
            )

        # Continuous race blocks:
        # from 10 min before each deadline until 10 min before next race.
        for idx, (race, race_dt) in enumerate(race_dts):
            block_start = max(
                pre_start,
                race_dt - datetime.timedelta(minutes=10),
            )

            if idx + 1 < len(race_dts):
                next_dt = race_dts[idx + 1][1]
                block_stop = next_dt - datetime.timedelta(minutes=10)
            else:
                block_stop = race_dt + datetime.timedelta(minutes=30)

            if block_stop <= block_start:
                block_stop = race_dt + datetime.timedelta(minutes=15)

            race_no = race.get("race", "")
            race_time = race.get("time", "")

            title_parts = [
                "🚤",
                v_name,
                f"{race_no}R",
                f"{race_time}発走",
                f"{emoji}{day_type}",
            ]
            if event_title:
                title_parts.append(event_title)
            title = " ".join(x for x in title_parts if x).strip()

            desc_lines = [
                f"🚤 ボートレース {v_name}",
                f"{emoji} 開催区分: {day_type}",
                f"⏰ 発走予定: {race_time}",
                f"📅 {today_display}",
            ]
            if event_title:
                desc_lines.insert(1, f"📢 {event_title}")

            add_programme(
                tv,
                tvg_id,
                block_start,
                min(block_stop, day_end),
                title,
                "\n".join(desc_lines),
            )

        finish = race_dts[-1][1] + datetime.timedelta(minutes=30)
        if finish < day_end:
            add_programme(
                tv,
                tvg_id,
                finish,
                day_end,
                f"🏁 終了 {v_name} {emoji}{day_type}",
                f"{v_name}の本日のボートレースは終了しました。",
            )

    return True



def build_boat_epg(
    tv,
    date_str,
    boat_today,
    JST,
    today_str,
    today_display,
):
    for v_name, tvg_id in BOAT_MAP.items():
        day_start = datetime.datetime.strptime(
            f"{date_str} 01:00", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        day_end = datetime.datetime.strptime(
            f"{date_str} 23:59", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        if date_str != today_str:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"📅 {v_name} ボートレース",
                f"{today_display} {v_name} ボートレース",
            )
            continue

        info = boat_today.get(v_name, {})

        if not isinstance(info, dict) or not info.get("live"):
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"💤 本日非開催 {v_name}（ボートレース）",
                f"{v_name}のライブ配信URLは取得されていません。",
            )
            continue

        start_text = info.get("start")
        end_text = info.get("end")
        day_type = info.get("day_type", "開催")
        emoji = info.get("emoji", "🚤")

        if not start_text or not end_text:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"🔴 LIVE {v_name} 🚤ボートレース",
                f"🚤 ボートレース {v_name}\n"
                f"✅ 配信URL取得済み\n"
                f"📅 {today_display}",
            )
            continue

        start_dt = datetime.datetime.strptime(
            f"{date_str} {start_text}", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        end_dt = datetime.datetime.strptime(
            f"{date_str} {end_text}", "%Y%m%d %H:%M"
        ).replace(tzinfo=JST)

        if end_dt <= start_dt:
            end_dt += datetime.timedelta(days=1)

        pre_start = start_dt - datetime.timedelta(minutes=10)

        desc = (
            f"🚤 ボートレース {v_name}\n"
            f"⏰ 配信予定: {start_text}～{end_text}\n"
            f"{emoji} 開催区分: {day_type}\n"
            f"📅 {today_display}"
        )

        if day_start < pre_start:
            add_programme(
                tv,
                tvg_id,
                day_start,
                pre_start,
                f"⏳ 待機 {v_name} {emoji}{day_type} {start_text}開始",
                desc,
            )

        if pre_start < start_dt:
            add_programme(
                tv,
                tvg_id,
                max(pre_start, day_start),
                start_dt,
                f"⏳ まもなく開始 {v_name} {emoji}{day_type}",
                desc,
            )

        add_programme(
            tv,
            tvg_id,
            start_dt,
            end_dt,
            f"🔴 LIVE {v_name} {emoji}{day_type} 🚤ボートレース",
            desc,
        )

        if end_dt < day_end:
            add_programme(
                tv,
                tvg_id,
                end_dt,
                day_end,
                f"🏁 終了 {v_name} {emoji}{day_type}",
                f"{v_name}の本日のライブ配信は終了しました。",
            )



# -------------------------------------------------
# KEIRIN.JP future schedule support
# Future days use official monthly schedule metadata:
# venue / grade / day pattern / event day.
# Exact race times are replaced by provisional start times.
# -------------------------------------------------

KEIRIN_JP_SCHEDULE_URL = (
    "https://keirin.jp/pc/raceschedule?scym={month}&scyy={year}"
)

KEIRIN_FUTURE_GRADE_BY_SRC = {
    "ico_f1.png": "F1",
    "ico_f2.png": "F2",
    "ico_g1.png": "G1",
    "ico_g2.png": "G2",
    "ico_g3.png": "G3",
}

KEIRIN_FUTURE_TYPE_BY_SRC = {
    "ico_kaisai_3.png": ("ナイター", "🌙"),
    "ico_kaisai_5.png": ("ミッドナイト", "⭐"),
    "ico_kaisai_8.png": ("モーニング", "🌅"),
}

KEIRIN_FUTURE_START = {
    "モーニング": "08:30",
    "デイ": "10:30",
    "ナイター": "15:00",
    "ミッドナイト": "20:30",
}


class KeirinScheduleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_tr = False
        self.in_td = False
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "tr":
            self.in_tr = True
            self.row = []

        elif tag == "td" and self.in_tr:
            self.in_td = True
            try:
                colspan = int(attrs.get("colspan", "1") or "1")
            except Exception:
                colspan = 1

            self.cell = {
                "text": [],
                "imgs": [],
                "colspan": max(1, colspan),
            }

        elif tag == "img" and self.in_td and self.cell is not None:
            self.cell["imgs"].append(
                {
                    "src": attrs.get("src", ""),
                    "alt": attrs.get("alt", ""),
                    "title": attrs.get("title", ""),
                }
            )

    def handle_data(self, data):
        if self.in_td and self.cell is not None:
            value = re.sub(r"\s+", " ", data).strip()
            if value:
                self.cell["text"].append(value)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_td:
            self.in_td = False
            self.row.append(self.cell)
            self.cell = None

        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            if self.row:
                self.rows.append(self.row)
            self.row = []


def keirin_schedule_venue(cell):
    text = re.sub(r"\s+", "", " ".join(cell.get("text", [])))
    for venue in KEIRIN_MAP:
        if venue in text:
            return venue
    return ""


def classify_keirin_future_cell(cell):
    grade = ""
    day_type = "デイ"
    emoji = "☀️"

    combined_text = " ".join(
        cell.get("text", [])
        + [x.get("alt", "") for x in cell.get("imgs", [])]
        + [x.get("title", "") for x in cell.get("imgs", [])]
    )

    if "ミッドナイト" in combined_text:
        day_type, emoji = "ミッドナイト", "⭐"
    elif "モーニング" in combined_text:
        day_type, emoji = "モーニング", "🌅"
    elif "ナイター" in combined_text:
        day_type, emoji = "ナイター", "🌙"

    icons = []

    for img in cell.get("imgs", []):
        base = img.get("src", "").rsplit("/", 1)[-1]
        icons.append(base)

        if base in KEIRIN_FUTURE_GRADE_BY_SRC:
            grade = KEIRIN_FUTURE_GRADE_BY_SRC[base]

        if base in KEIRIN_FUTURE_TYPE_BY_SRC:
            day_type, emoji = KEIRIN_FUTURE_TYPE_BY_SRC[base]

    # Dokanto! and other auxiliary icons are intentionally ignored.
    return {
        "has_event": bool(grade),
        "grade": grade,
        "day_type": day_type,
        "emoji": emoji,
        "icons": icons,
    }


def keirin_event_day_label(index_in_span, span):
    if span <= 1:
        return ""
    if index_in_span == 0:
        return "初日"
    if index_in_span == span - 1:
        return "最終日"
    return f"{index_in_span + 1}日目"


def fetch_keirin_future_month(year, month):
    url = KEIRIN_JP_SCHEDULE_URL.format(
        year=year,
        month=f"{month:02d}",
    )
    source = fetch_text(url, f"KEIRIN.JP schedule {year}-{month:02d}")

    if not source:
        return {}

    parser = KeirinScheduleParser()
    parser.feed(source)

    result = {}

    for row in parser.rows:
        if len(row) < 2:
            continue

        venue = keirin_schedule_venue(row[0])
        if not venue:
            continue

        logical_day = 1

        for cell in row[1:]:
            span = max(1, int(cell.get("colspan", 1)))
            info = classify_keirin_future_cell(cell)

            for offset in range(span):
                day = logical_day + offset
                if day > 31:
                    break

                if info["has_event"]:
                    date_str = f"{year:04d}{month:02d}{day:02d}"
                    result.setdefault(date_str, {})[venue] = {
                        **info,
                        "event_day": keirin_event_day_label(offset, span),
                        "span": span,
                    }

            logical_day += span

            if logical_day > 31:
                break

    return result


def build_keirin_future_epg(
    tv,
    target_date,
    month_schedule,
    JST,
    today_display,
):
    date_str = target_date.strftime("%Y%m%d")
    day_start = datetime.datetime.strptime(
        f"{date_str} 01:00",
        "%Y%m%d %H:%M",
    ).replace(tzinfo=JST)
    day_end = datetime.datetime.strptime(
        f"{date_str} 23:59",
        "%Y%m%d %H:%M",
    ).replace(tzinfo=JST)

    venues = month_schedule.get(date_str, {})
    handled = 0

    for venue, tvg_id in KEIRIN_MAP.items():
        info = venues.get(venue)

        if not info:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"💤 本日非開催 {venue}（競輪）",
                f"KEIRIN.JP開催日程で{today_display}の開催予定はありません。",
            )
            continue

        handled += 1

        grade = info.get("grade", "")
        day_type = info.get("day_type", "デイ")
        emoji = info.get("emoji", "☀️")
        event_day = info.get("event_day", "")
        start_text = KEIRIN_FUTURE_START.get(day_type, "10:30")

        start_dt = datetime.datetime.strptime(
            f"{date_str} {start_text}",
            "%Y%m%d %H:%M",
        ).replace(tzinfo=JST)

        if day_start < start_dt:
            add_programme(
                tv,
                tvg_id,
                day_start,
                start_dt,
                f"⏳ 待機 {venue} 【{grade}】 {emoji}{day_type}",
                "\n".join(
                    x
                    for x in [
                        f"🚲 競輪 {venue}",
                        f"🏆 開催種別: {grade}" if grade else "",
                        f"{emoji} 開催パターン: {day_type}",
                        f"📅 {event_day}" if event_day else "",
                        f"⏰ 仮開始: {start_text}",
                        f"📅 {today_display}",
                    ]
                    if x
                ),
            )

        title_parts = [
            f"【{grade}】" if grade else "",
            venue,
            f"{emoji}{day_type}",
            event_day,
            "開催予定",
        ]
        title = " ".join(x for x in title_parts if x)

        desc_lines = [
            f"🚲 競輪 {venue}",
            f"🏆 開催種別: {grade}" if grade else "",
            f"{emoji} 開催パターン: {day_type}",
            f"📅 開催日次: {event_day}" if event_day else "",
            f"⏰ 仮開始: {start_text}",
            "未来日のため発走時刻は仮予定です。",
            "当日08:00更新で実際の各R発走時刻EPGへ切り替えます。",
            f"📅 {today_display}",
        ]

        add_programme(
            tv,
            tvg_id,
            start_dt,
            day_end,
            title,
            "\n".join(x for x in desc_lines if x),
        )

    print(
        f"KEIRIN FUTURE EPG {date_str}: "
        f"{handled}場を開催予定として生成"
    )


def build_future_placeholder(
    tv,
    date_str,
    target_map,
    category_label,
    category_icon,
    JST,
    today_display,
):
    """Future dates without race JSON: show a neutral schedule placeholder."""
    day_start = datetime.datetime.strptime(
        f"{date_str} 01:00", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)
    day_end = datetime.datetime.strptime(
        f"{date_str} 23:59", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)

    for v_name, tvg_id in target_map.items():
        add_programme(
            tv,
            tvg_id,
            day_start,
            day_end,
            f"📅 {v_name}（{category_label}）",
            f"{category_icon} {category_label} {v_name}\n"
            f"📅 {today_display}\n"
            "当日データ取得時に詳細EPGへ自動更新します。",
        )


def build_stream_channel_placeholder(
    tv,
    date_str,
    channel_names,
    JST,
    today_display,
):
    """Channels such as JRA official/Green Channel that have no race JSON."""
    day_start = datetime.datetime.strptime(
        f"{date_str} 01:00", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)
    day_end = datetime.datetime.strptime(
        f"{date_str} 23:59", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)

    for v_name in channel_names:
        tvg_id = KEIBA_MAP.get(v_name)
        if not tvg_id:
            continue
        add_programme(
            tv,
            tvg_id,
            day_start,
            day_end,
            f"📺 {v_name}",
            f"📺 {v_name}\n📅 {today_display}",
        )



def jra_calendar_url(target_date):
    year = target_date.strftime("%Y")
    month = str(int(target_date.strftime("%m")))
    mmdd = target_date.strftime("%m%d")
    return f"https://www.jra.go.jp/keiba/calendar{year}/{year}/{month}/{mmdd}.html"


JRA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.7,en;q=0.6",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}


def fetch_jra_html(url, label="JRA"):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)
    )

    def _open(target_url, referer=None):
        headers = dict(JRA_HEADERS)
        if referer:
            headers["Referer"] = referer

        req = urllib.request.Request(target_url, headers=headers)
        with opener.open(req, timeout=30) as response:
            body = response.read()
            ctype = response.headers.get("Content-Type", "")

        encodings = []
        m = re.search(r"charset=([A-Za-z0-9_\-]+)", ctype, flags=re.I)
        if m:
            encodings.append(m.group(1))

        head = body[:5000].decode("ascii", errors="ignore")
        m = re.search(r'charset=["\']?\s*([A-Za-z0-9_\-]+)', head, flags=re.I)
        if m:
            encodings.append(m.group(1))

        encodings += ["utf-8", "cp932", "shift_jis", "euc_jp"]

        seen = set()
        best_text = ""
        best_score = -1

        for enc in encodings:
            enc = enc.lower()
            if enc in seen:
                continue
            seen.add(enc)

            try:
                decoded = body.decode(enc)
            except Exception:
                continue

            score = sum(
                decoded.count(word)
                for word in (
                    "東京", "中山", "新潟", "福島", "京都",
                    "阪神", "中京", "小倉", "札幌", "函館",
                    "競馬番組", "レース番号", "発走時刻",
                )
            )
            if score > best_score:
                best_score = score
                best_text = decoded

        return best_text or body.decode("utf-8", errors="ignore")

    try:
        try:
            _open("https://www.jra.go.jp/", "https://www.google.com/")
        except Exception as e:
            print(f"{label}: top page prime failed: {e}")

        return _open(
            url,
            "https://www.jra.go.jp/keiba/calendar/",
        )
    except Exception as e:
        print(f"{label}: 取得失敗: {e}")
        return ""


def _extract_jra_races_from_section(section):
    races = {}

    race_re = re.compile(
        r"(\d{1,2})\s*レース\s+(.*?)\s+([0-2]?\d)\s*時\s*([0-5]\d)\s*分",
        flags=re.S,
    )

    for m in race_re.finditer(section):
        rn = int(m.group(1))
        if not 1 <= rn <= 12:
            continue

        name = re.sub(r"\s+", " ", m.group(2)).strip()
        if len(name) > 180:
            name = name[:180] + "…"

        races[rn] = {
            "race": str(rn),
            "time": f"{int(m.group(3)):02d}:{m.group(4)}",
            "name": name or "JRA競走",
        }

    return [races[n] for n in sorted(races)]


def fetch_jra_day(target_date):
    url = jra_calendar_url(target_date)
    source = fetch_jra_html(url, f"JRA {target_date:%Y%m%d}")
    if not source:
        return {}

    plain = strip_html_tags(source)

    # Actual meeting blocks on the JRA programme page are headed like:
    # "2回新潟7日", "2回中京7日", "1回札幌7日".
    # Parsing only these headings avoids false positives from navigation links.
    meeting_re = re.compile(
        r"(\d+)\s*回\s*"
        r"(東京|中山|新潟|福島|京都|阪神|中京|小倉|札幌|函館)"
        r"\s*(\d+)\s*日"
    )
    headings = list(meeting_re.finditer(plain))

    out = {}

    for i, match in enumerate(headings):
        venue = match.group(2)
        section_start = match.end()
        section_end = (
            headings[i + 1].start()
            if i + 1 < len(headings)
            else len(plain)
        )

        section = plain[section_start:section_end]
        races = _extract_jra_races_from_section(section)

        # A normal JRA meeting should have a substantial race card.
        # Keep it only when enough races were actually parsed.
        if len(races) >= 5:
            out[venue] = races

    print(
        f"JRA {target_date:%Y%m%d}: "
        + (
            ", ".join(f"{venue}={len(races)}R" for venue, races in out.items())
            if out
            else "開催場なし"
        )
    )

    return out


def build_jra_stream_epg(tv, target_date, JST, today_display):
    date_str = target_date.strftime("%Y%m%d")
    day_start = datetime.datetime.strptime(
        f"{date_str} 01:00", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)
    day_end = datetime.datetime.strptime(
        f"{date_str} 23:59", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)

    by_venue = fetch_jra_day(target_date)
    by_stream = {k: [] for k in JRA_STREAM_MAP}

    for venue, races in by_venue.items():
        stream = JRA_VENUE_TO_STREAM.get(venue)
        if stream:
            by_stream[stream].append((venue, races))

    for stream_name, tvg_id in JRA_STREAM_MAP.items():
        meetings = by_stream.get(stream_name, [])

        if not meetings:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"💤 JRA 本日使用なし {stream_name}",
                f"JRA公式で{today_display}の対象開催を確認できませんでした。",
            )
            continue

        flat = []

        for venue, races in meetings:
            for race in races:
                try:
                    dt = datetime.datetime.strptime(
                        f"{date_str} {race['time']}",
                        "%Y%m%d %H:%M",
                    ).replace(tzinfo=JST)
                except Exception:
                    continue

                flat.append((dt, venue, race))

        flat.sort(key=lambda x: x[0])

        if not flat:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                f"📅 JRA 開催予定 {stream_name}",
                f"JRA公式で開催を確認しました。\n📅 {today_display}",
            )
            continue

        pre = max(
            day_start,
            flat[0][0] - datetime.timedelta(minutes=20),
        )

        if day_start < pre:
            add_programme(
                tv,
                tvg_id,
                day_start,
                pre,
                f"⏳ 待機 {stream_name} / {flat[0][1]}",
                f"🏇 JRA {flat[0][1]}\n"
                f"1R発走予定 {flat[0][2]['time']}\n"
                f"📅 {today_display}",
            )

        for i, (dt, venue, race) in enumerate(flat):
            block_start = max(
                pre,
                dt - datetime.timedelta(minutes=10),
            )

            if i + 1 < len(flat):
                block_stop = flat[i + 1][0] - datetime.timedelta(minutes=10)
            else:
                block_stop = dt + datetime.timedelta(minutes=30)

            if block_stop <= block_start:
                block_stop = dt + datetime.timedelta(minutes=15)

            title = (
                f"🏇 {venue} {race['race']}R "
                f"{race['time']}発走 {race.get('name', 'JRA競走')}"
            )

            desc = (
                f"🏇 JRA {venue}\n"
                f"⏰ 発走予定: {race['time']}\n"
                f"📢 {race.get('name', '')}\n"
                f"📅 {today_display}"
            )

            add_programme(
                tv,
                tvg_id,
                block_start,
                min(block_stop, day_end),
                title,
                desc,
            )

        finish = flat[-1][0] + datetime.timedelta(minutes=30)

        if finish < day_end:
            venues_text = "・".join(dict.fromkeys(v for _, v, _ in flat))
            add_programme(
                tv,
                tvg_id,
                finish,
                day_end,
                f"🏁 JRA 本日開催終了 {stream_name}",
                f"{venues_text}の本日のJRA開催は終了しました。",
            )

    print(
        "JRA EPG:",
        ", ".join(
            f"{name}={len(meetings)}場"
            for name, meetings in by_stream.items()
        ),
    )



# -------------------------------------------------
# AutoRace.JP future calendar support
# Future days use the official monthly Calendar API.
# Only calendar[].race means a home-track event; outside[] is ignored.
# -------------------------------------------------
AUTORACE_CALENDAR_URL = "https://autorace.jp/race_info/XML/Calendar?date={year}-{month:02d}"

def fetch_autorace_future_month(year, month):
    data = fetch_json(
        AUTORACE_CALENDAR_URL.format(year=year, month=month),
        f"AUTORACE FUTURE {year}-{month:02d}",
    )
    result = {}
    if not isinstance(data, dict):
        return result

    body = data.get("body", [])
    if not isinstance(body, list):
        return result

    for place in body:
        if not isinstance(place, dict):
            continue
        venue = re.sub(r"\s+", "", str(place.get("placeName", "")))
        if venue not in AUTO_MAP:
            continue
        for day in place.get("calendar", []) or []:
            if not isinstance(day, dict):
                continue
            race = day.get("race")
            # [] means no home-track event. outside[] is off-track sales only.
            if not isinstance(race, dict) or not race:
                continue
            iso_date = str(day.get("date", ""))
            date_str = iso_date.replace("-", "")
            if len(date_str) != 8:
                continue
            result.setdefault(date_str, {})[venue] = race
    return result

def build_autorace_future_epg(tv, target_date, month_schedule, JST, today_display):
    date_str = target_date.strftime("%Y%m%d")
    day_start = datetime.datetime.strptime(
        f"{date_str} 01:00", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)
    day_end = datetime.datetime.strptime(
        f"{date_str} 23:59", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)

    venues = month_schedule.get(date_str, {})
    handled = 0
    for venue, tvg_id in AUTO_MAP.items():
        race = venues.get(venue)
        if not race:
            add_programme(
                tv, tvg_id, day_start, day_end,
                f"💤 本日非開催 {venue}（オートレース）",
                f"AutoRace.JP公式カレンダーで{today_display}の本場開催はありません。",
            )
            continue

        handled += 1
        grade = clean_epg_meta_text(race.get("gradeName", ""))
        title = clean_epg_meta_text(race.get("title", "")) or clean_epg_meta_text(race.get("titleShort", ""))
        day_type = clean_epg_meta_text(race.get("nighterName", "")) or "デイ"
        emoji = day_emoji(day_type)
        event_day = race.get("paragraphDay", "")
        start_text = str(race.get("liveStartTime", "") or "").strip()
        end_text = str(race.get("liveEndTime", "") or "").strip()

        try:
            start_dt = datetime.datetime.strptime(
                f"{date_str} {start_text}", "%Y%m%d %H:%M"
            ).replace(tzinfo=JST)
            end_dt = datetime.datetime.strptime(
                f"{date_str} {end_text}", "%Y%m%d %H:%M"
            ).replace(tzinfo=JST)
            if end_dt <= start_dt:
                end_dt += datetime.timedelta(days=1)
        except Exception:
            start_dt, end_dt = day_start, day_end

        if day_start < start_dt:
            add_programme(
                tv, tvg_id, day_start, start_dt,
                f"⏳ 開催待ち {venue} {emoji}{day_type}",
                f"🏍️ オートレース {venue}\n📢 {title}\n📅 {today_display}",
            )

        parts = ["📅 開催予定", venue, f"{emoji}{day_type}"]
        if grade:
            parts.append(f"【{grade}】")
        if title:
            parts.append(title)
        if event_day:
            parts.append(f"{event_day}日目")
        desc = [f"🏍️ オートレース {venue}"]
        if grade:
            desc.append(f"🏆 グレード: {grade}")
        if title:
            desc.append(f"📢 開催名: {title}")
        if event_day:
            desc.append(f"📅 開催日次: {event_day}日目")
        if start_text and end_text:
            desc.append(f"⏰ 公式LIVE予定: {start_text}～{end_text}")
        desc.append(f"📅 {today_display}")
        add_programme(tv, tvg_id, start_dt, min(end_dt, day_end), " ".join(parts), "\n".join(desc))

        if end_dt < day_end:
            add_programme(
                tv, tvg_id, end_dt, day_end,
                f"🏁 終了 {venue} {emoji}{day_type}",
                f"{venue}の{today_display}の開催予定時間は終了しました。",
            )

    print(f"AUTORACE FUTURE EPG {date_str}: {handled}場を開催予定として生成")
    return True

def build_epg_xml():
    tv = ET.Element(
        "tv",
        {"generator-info-name": "CombinedEPGGenerator"},
    )

    JST = datetime.timezone(datetime.timedelta(hours=9))

    boat_today = load_boatrace_today()
    keiba_schedule = load_keiba_schedule()
    keirin_schedule = load_keirin_schedule()
    autorace_schedule = load_autorace_schedule()

    today_str = datetime.datetime.now(JST).strftime("%Y%m%d")

    all_channels = {
        **KEIRIN_MAP,
        **KEIBA_MAP,
        **AUTO_MAP,
        **BOAT_MAP,
        **JRA_STREAM_MAP,
        GCH_DISPLAY_NAME: GCH_TVG_ID,
    }

    for v_name, tvg_id in all_channels.items():
        channel = ET.SubElement(tv, "channel", id=tvg_id)
        ET.SubElement(channel, "display-name").text = v_name

    today_date = datetime.datetime.now(JST).date()
    boat_week = fetch_boat_week_schedule(today_date, EPG_DAYS)
    nar_future = fetch_nar_epg_days(today_date, EPG_DAYS)

    # AutoRace.JP monthly calendar for future-day EPG.
    autorace_future_months = {}
    for offset in range(1, EPG_DAYS):
        d = today_date + datetime.timedelta(days=offset)
        key = (d.year, d.month)
        if key not in autorace_future_months:
            autorace_future_months[key] = fetch_autorace_future_month(d.year, d.month)

    # KEIRIN.JP monthly schedule for future-day provisional EPG.
    keirin_future_months = {}
    for offset in range(1, EPG_DAYS):
        d = today_date + datetime.timedelta(days=offset)
        key = (d.year, d.month)
        if key not in keirin_future_months:
            keirin_future_months[key] = fetch_keirin_future_month(
                d.year,
                d.month,
            )

    for day_offset in range(EPG_DAYS):
        target_date = today_date + datetime.timedelta(days=day_offset)
        date_str = target_date.strftime("%Y%m%d")
        today_display = target_date.strftime("%Y年%m月%d日")
        is_today = (day_offset == 0)

        # -------------------------------------------------
        # 競輪
        # 今日: JSONの日付一致なら各R自動EPG。
        # 未来: 「非開催」と断定せず、当日更新待ちのプレースホルダー。
        # -------------------------------------------------
        if is_today:
            used_auto_keirin = build_keirin_race_epg(
                tv,
                date_str,
                keirin_schedule,
                JST,
                today_display,
            )
            if not used_auto_keirin:
                build_manual_category(
                    tv,
                    date_str,
                    "keirin",
                    KEIRIN_MAP,
                    {},
                    JST,
                    today_display,
                )
        else:
            month_schedule = keirin_future_months.get(
                (target_date.year, target_date.month),
                {},
            )
            build_keirin_future_epg(
                tv,
                target_date,
                month_schedule,
                JST,
                today_display,
            )

        # -------------------------------------------------
        # 競馬
        # 今日: JSONの日付一致なら各R自動EPG。
        # 未来: 決め打ちせずプレースホルダー。
        # -------------------------------------------------
        if is_today:
            used_auto_keiba = build_keiba_race_epg(
                tv,
                date_str,
                keiba_schedule,
                JST,
                today_display,
            )
            if not used_auto_keiba:
                regular_keiba_map = dict(KEIBA_MAP)
                build_manual_category(
                    tv,
                    date_str,
                    "keiba",
                    regular_keiba_map,
                    {},
                    JST,
                    today_display,
                )
        else:
            used_nar_future = build_keiba_race_epg(
                tv,
                date_str,
                nar_future.get(date_str, {}),
                JST,
                today_display,
            )
            if not used_nar_future:
                regular_keiba_map = dict(KEIBA_MAP)
                build_future_placeholder(
                    tv,
                    date_str,
                    regular_keiba_map,
                    "競馬",
                    "🏇",
                    JST,
                    today_display,
                )

        # JRA EAST / WEST / HOKKAIDO はJRA公式から3日分を生成。
        # GCHは全日ループ終了後に guides.xml から3日分だけ統合する。
        build_jra_stream_epg(
            tv,
            target_date,
            JST,
            today_display,
        )

        # -------------------------------------------------
        # オートレース
        # -------------------------------------------------
        if is_today:
            used_auto_autorace = build_autorace_race_epg(
                tv,
                date_str,
                autorace_schedule,
                JST,
                today_display,
            )
            if not used_auto_autorace:
                build_manual_category(
                    tv,
                    date_str,
                    "auto",
                    AUTO_MAP,
                    {},
                    JST,
                    today_display,
                )
        else:
            month_schedule = autorace_future_months.get(
                (target_date.year, target_date.month),
                {},
            )
            build_autorace_future_epg(
                tv,
                target_date,
                month_schedule,
                JST,
                today_display,
            )

        # -------------------------------------------------
        # ボートレース
        # BOAT RACE公式サイトの指定日開催一覧 + raceindex を使い、
        # 今日から明後日まで（3日分）開催場と1R～12R発走予定を自動EPG化。
        # 公式ページ取得失敗時だけ従来JSON方式へフォールバック。
        # -------------------------------------------------
        used_boat_official = build_boat_race_epg(
            tv,
            date_str,
            boat_week,
            JST,
            today_display,
        )

        if not used_boat_official:
            build_boat_epg(
                tv,
                date_str,
                boat_today,
                JST,
                today_str,
                today_display,
            )

    # -------------------------------------------------
    # グリーンチャンネル
    # karenda-jp guides.xml から該当チャンネルだけ3日分抽出して統合。
    # -------------------------------------------------
    gch_programme_count = import_gch_from_guides(
        tv,
        today_date,
        EPG_DAYS,
        JST,
    )

    tree = ET.ElementTree(tv)

    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ")

    tree.write(
        "epg.xml",
        encoding="utf-8",
        xml_declaration=True,
    )

    boat_live_count = sum(
        1
        for info in boat_today.values()
        if isinstance(info, dict) and info.get("live")
    )

    print("")
    print("============================")
    print("EPG生成完了")
    print(f"ボートLIVE: {boat_live_count} / 24")
    print(f"ボートEPG: BOAT RACE公式 3日分を自動取得")
    print("競馬: 当日はkeiba_schedule.json、未来2日はNAR公式を自動取得")
    print("競輪: keirin_schedule.json 優先")
    print("オート: autorace_schedule.json 優先")
    print("JRA: EAST / WEST / HOKKAIDOをJRA公式から3日分生成")
    print(f"GCH: guides.xmlから3日分を抽出・統合 ({gch_programme_count}番組)")
    print("出力: epg.xml")
    print("============================")


if __name__ == "__main__":
    build_epg_xml()
