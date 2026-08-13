import datetime
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))

KEIRIN_JSON = Path("keirin_today.json")
KEIBA_JSON = Path("keiba_today.json")
AUTORACE_JSON = Path("autorace_today.json")
BOAT_JSON = Path("boatrace_today.json")
JRA_JSON = Path("jra_today.json")
OUT_XML = Path("epg.xml")

KEIRIN_MAP = {
    "函館": "keirin.hakodate", "青森": "keirin.aomori", "いわき平": "keirin.iwakitaira", "弥彦": "keirin.yahiko",
    "前橋": "keirin.maebashi", "取手": "keirin.toride", "宇都宮": "keirin.utsunomiya", "大宮": "keirin.omiya",
    "西武園": "keirin.seibuen", "京王閣": "keirin.keiogatsu", "立川": "keirin.tachikawa", "松戸": "keirin.matsudo",
    "川崎": "keirin.kawasaki", "平塚": "keirin.hiratsuka", "小田原": "keirin.odawara", "伊東": "keirin.ito",
    "静岡": "keirin.shizuoka", "名古屋": "keirin.nagoya", "岐阜": "keirin.gifu", "大垣": "keirin.ogaki",
    "豊橋": "keirin.toyohashi", "富山": "keirin.toyama", "松阪": "keirin.matsusaka", "四日市": "keirin.yokkaichi",
    "福井": "keirin.fukui", "奈良": "keirin.nara", "向日町": "keirin.mukomachi", "和歌山": "keirin.wakayama",
    "岸和田": "keirin.kishiwada", "玉野": "keirin.tamano", "広島": "keirin.hiroshima", "防府": "keirin.hofu",
    "高松": "keirin.takamatsu", "小松島": "keirin.komatsushima", "高知": "keirin.kochi", "松山": "keirin.matsuyama",
    "小倉": "keirin.kokura", "久留米": "keirin.kurume", "武雄": "keirin.takeo", "佐世保": "keirin.sasebo",
    "別府": "keirin.beppu", "熊本": "keirin.kumamoto", "千葉": "keirin.pist6",
}

KEIBA_MAP = {
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

AUTO_MAP = {
    "川口": "auto.kawaguchi",
    "伊勢崎": "auto.isesaki",
    "浜松": "auto.hamamatsu",
    "飯塚": "auto.iizuka",
    "山陽": "auto.sanyo",
}


JRA_CHANNEL_MAP = {
    "gch": "jra.gch",
    "east": "jra.east",
    "west": "jra.west",
    "hokkaido": "jra.hokkaido",
}

BOAT_MAP = {
    "01 桐生": "boat.kiryu", "02 戸田": "boat.toda", "03 江戸川": "boat.edogawa", "04 平和島": "boat.heiwajima",
    "05 多摩川": "boat.tamagawa", "06 浜名湖": "boat.hamanako", "07 蒲郡": "boat.gamagori", "08 常滑": "boat.tokoname",
    "09 津": "boat.tsu", "10 三国": "boat.mikuni", "11 びわこ": "boat.biwako", "12 住之江": "boat.suminoe",
    "13 尼崎": "boat.amagasaki", "14 鳴門": "boat.naruto", "15 丸亀": "boat.marugame", "16 児島": "boat.kojima",
    "17 宮島": "boat.miyajima", "18 徳山": "boat.tokuyama", "19 下関": "boat.shimonoseki", "20 若松": "boat.wakamatsu",
    "21 芦屋": "boat.ashiya", "22 福岡": "boat.fukuoka", "23 唐津": "boat.karatsu", "24 大村": "boat.omura",
}


def load_json(path: Path):
    if not path.exists():
        print(f"WARNING: {path} がありません")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"WARNING: {path} 読み込み失敗: {e}")
        return {}


def xml_time(dt):
    return dt.strftime("%Y%m%d%H%M%S +0900")


def add_programme(tv, channel, start, stop, title, desc=""):
    if stop <= start:
        return
    p = ET.SubElement(
        tv,
        "programme",
        start=xml_time(start),
        stop=xml_time(stop),
        channel=channel,
    )
    ET.SubElement(p, "title", lang="ja").text = title
    if desc:
        ET.SubElement(p, "desc", lang="ja").text = desc


def day_bounds(date_str):
    day_start = datetime.datetime.strptime(
        f"{date_str} 01:00", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)
    day_end = datetime.datetime.strptime(
        f"{date_str} 23:59", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)
    return day_start, day_end


def parse_hm(date_str, hm):
    return datetime.datetime.strptime(
        f"{date_str} {hm}", "%Y%m%d %H:%M"
    ).replace(tzinfo=JST)


def clean_text(value):
    s = re.sub(r"\s+", " ", str(value or "")).strip()
    return s.strip(" \t\r\n-|｜()（）[]【】『』「」・:：,，.。")


def make_nonheld(tv, date_str, venue_map, label, icon, held_names):
    day_start, day_end = day_bounds(date_str)
    for venue, tvg_id in venue_map.items():
        if venue in held_names:
            continue
        add_programme(
            tv,
            tvg_id,
            day_start,
            day_end,
            f"💤 本日非開催 {venue}（{label}）",
            f"{icon} 本日は{venue}での{label}開催情報を取得していません。",
        )


def build_standard_race_epg(tv, date_str, data, venue_map, sport, sport_icon):
    """
    競輪・地方競馬・オート共通。
    JSON形式:
      {"date":"YYYYMMDD","venues":{場名:{day_type,races:[...]}}}
    """
    venues = data.get("venues", {}) if data.get("date") == date_str else {}
    handled = set()
    day_start, day_end = day_bounds(date_str)

    for venue, info in venues.items():
        tvg_id = venue_map.get(venue) or info.get("tvg_id", "")
        if not tvg_id:
            print(f"{sport}: tvg-id未登録: {venue}")
            continue

        races = []
        for r in info.get("races", []):
            try:
                dt = parse_hm(date_str, r.get("time", ""))
            except Exception:
                continue
            races.append((r, dt))

        races.sort(key=lambda x: x[1])
        if not races:
            continue

        handled.add(venue)

        day_type = clean_text(info.get("day_type", "デイ")) or "デイ"
        day_icon = clean_text(info.get("day_emoji", "")) or {
            "モーニング": "🌅",
            "薄暮": "🌇",
            "ナイター": "🌙",
            "ミッドナイト": "⭐",
            "アフター5": "🌆",
            "アーリー": "🌅",
        }.get(day_type, "☀️")

        grade = clean_text(info.get("grade", ""))
        event_name = clean_text(info.get("event_name", ""))
        event_day = clean_text(info.get("event_day", ""))

        first_dt = races[0][1]
        pre_start = max(day_start, first_dt - datetime.timedelta(minutes=20))

        if day_start < pre_start:
            add_programme(
                tv,
                tvg_id,
                day_start,
                pre_start,
                f"⏳ 待機 {venue} {day_icon}{day_type}",
                "\n".join(
                    x for x in [
                        f"{sport_icon} {sport} {venue}",
                        f"📢 {event_name}" if event_name else "",
                        f"📅 {event_day}" if event_day else "",
                        f"1R発走予定 {races[0][0].get('time', '')}",
                    ] if x
                ),
            )

        for idx, (race, start_time) in enumerate(races):
            lead = 10 if sport == "地方競馬" else 8
            block_start = max(pre_start, start_time - datetime.timedelta(minutes=lead))

            if idx + 1 < len(races):
                next_time = races[idx + 1][1]
                block_stop = next_time - datetime.timedelta(minutes=lead)
            else:
                block_stop = start_time + datetime.timedelta(minutes=30 if sport == "地方競馬" else 25)

            if block_stop <= block_start:
                block_stop = start_time + datetime.timedelta(minutes=12)

            race_no = race.get("race", "")
            race_time = race.get("time", "")
            race_name = clean_text(race.get("name", "")) or clean_text(race.get("race_type", "")) or "競走"
            race_type = clean_text(race.get("race_type", ""))
            icon = clean_text(race.get("icon", "")) or sport_icon
            main = bool(race.get("main"))
            girls = bool(race.get("girls"))

            title_parts = []
            if main:
                title_parts.append("🏆 MAIN")
            if girls:
                title_parts.append("💛")
            else:
                title_parts.append(icon)

            if grade and main:
                title_parts.append(f"【{grade}】")

            title_parts += [
                f"{venue} {race_no}R",
                f"{race_time}発走",
                race_name,
            ]

            if race_type and race_type not in race_name and race_type not in {"一般", "一般戦"}:
                title_parts.append(f"【{race_type}】")

            conditions = clean_text(race.get("conditions", ""))
            if conditions and conditions not in race_name and conditions != race_type:
                title_parts.append(conditions)

            desc = [
                f"{sport_icon} {sport} {venue}",
                f"{day_icon} 開催区分: {day_type}",
                f"⏰ 発走予定: {race_time}",
            ]
            if grade:
                desc.append(f"🏆 グレード: {grade}")
            if event_name:
                desc.append(f"📢 開催名: {event_name}")
            if event_day:
                desc.append(f"📅 開催日次: {event_day}")
            if race_type:
                desc.append(f"🏷️ 種別: {race_type}")
            if race_name:
                desc.append(f"📢 レース名: {race_name}")
            if conditions:
                desc.append(f"📋 条件: {conditions}")
            if girls:
                desc.append("💛 ガールズ")
            if bool(race.get("is_semi")) or "準決" in race_name:
                desc.append("🔥 準決勝")
            if bool(race.get("is_final")) or ("決勝" in race_name and "準決" not in race_name) or "優勝戦" in race_name:
                desc.append("🏆 決勝・優勝戦")
            if main:
                desc.append("🏆 メインレース")

            add_programme(
                tv,
                tvg_id,
                block_start,
                min(block_stop, day_end),
                " ".join(x for x in title_parts if x),
                "\n".join(desc),
            )

        finish = races[-1][1] + datetime.timedelta(minutes=30 if sport == "地方競馬" else 25)
        if finish < day_end:
            add_programme(
                tv,
                tvg_id,
                finish,
                day_end,
                f"🏁 終了 {venue} {day_icon}{day_type}",
                f"{venue}の本日の{sport}は終了しました。",
            )

    make_nonheld(tv, date_str, venue_map, sport, sport_icon, handled)
    print(f"{sport}: {len(handled)}場を各R単位で生成")


def build_boat_epg(tv, date_str, data):
    """
    boatrace_today.json はPowerShell側でepg_start/epg_end/titleを作成済み。
    それを最優先してそのままXMLTV化する。
    """
    day_start, day_end = day_bounds(date_str)

    for venue, tvg_id in BOAT_MAP.items():
        info = data.get(venue, {})
        if not isinstance(info, dict):
            info = {}

        races = info.get("races", [])
        held = bool(info.get("held")) or bool(races)
        day_type = clean_text(info.get("day_type", "")) or "開催"
        emoji = clean_text(info.get("emoji", "")) or "🚤"

        if not held:
            add_programme(
                tv,
                tvg_id,
                day_start,
                day_end,
                info.get("status_title") or f"⛔ {venue} 本日非開催",
                f"🚤 本日は{venue}でのボートレース開催予定はありません。",
            )
            continue

        valid = []
        for race in races:
            try:
                start_dt = datetime.datetime.strptime(
                    race.get("epg_start", ""), "%Y-%m-%d %H:%M"
                ).replace(tzinfo=JST)
                stop_dt = datetime.datetime.strptime(
                    race.get("epg_end", ""), "%Y-%m-%d %H:%M"
                ).replace(tzinfo=JST)
                if stop_dt > start_dt:
                    valid.append((race, start_dt, stop_dt))
            except Exception:
                continue

        if not valid:
            # 念のため通常時刻だけでも表示
            fallback = []
            for race in races:
                try:
                    dt = parse_hm(date_str, race.get("time", ""))
                    fallback.append((race, dt))
                except Exception:
                    pass

            if fallback:
                for idx, (race, dt) in enumerate(fallback):
                    start_dt = max(day_start, dt - datetime.timedelta(minutes=10))
                    stop_dt = (
                        fallback[idx + 1][1] - datetime.timedelta(minutes=10)
                        if idx + 1 < len(fallback)
                        else dt + datetime.timedelta(minutes=30)
                    )
                    title = race.get("title") or f"{emoji} {venue} {race.get('rno', race.get('race',''))}R【{race.get('time','')}】"
                    add_programme(tv, tvg_id, start_dt, min(stop_dt, day_end), title)
                finish = fallback[-1][1] + datetime.timedelta(minutes=30)
                if finish < day_end:
                    add_programme(tv, tvg_id, finish, day_end, f"🏁 {venue} 本日開催終了")
            else:
                add_programme(
                    tv, tvg_id, day_start, day_end,
                    f"📅 開催予定 {venue} {emoji}{day_type}",
                    f"🚤 {venue}は開催判定済みですが、レース時刻を取得できませんでした。",
                )
            continue

        first_start = valid[0][1]
        if day_start < first_start:
            first_race = valid[0][0]
            add_programme(
                tv,
                tvg_id,
                day_start,
                first_start,
                f"⏳ 待機 {venue} {emoji}{day_type} 1R【{first_race.get('time','')}】",
                f"🚤 ボートレース {venue}\n{emoji} 開催区分: {day_type}",
            )

        for race, start_dt, stop_dt in valid:
            race_no = race.get("rno", race.get("race", ""))
            race_time = race.get("time", "")
            race_name = clean_text(race.get("race_name", ""))

            title = clean_text(race.get("title", ""))
            if not title:
                title = f"{emoji} {venue} {race_no}R"
                if race_name:
                    title += f" {race_name}"
                title += f"【{race_time}】"

            desc = [
                f"🚤 ボートレース {venue}",
                f"{emoji} 開催区分: {day_type}",
                f"⏰ 締切予定: {race_time}",
            ]
            if race_name:
                desc.append(f"📢 レース名: {race_name}")

            add_programme(
                tv,
                tvg_id,
                max(start_dt, day_start),
                min(stop_dt, day_end),
                title,
                "\n".join(desc),
            )

        finish_start = valid[-1][2]
        try:
            if info.get("finish_start"):
                f = datetime.datetime.strptime(
                    info["finish_start"], "%Y-%m-%d %H:%M"
                ).replace(tzinfo=JST)
                finish_start = max(finish_start, f)
        except Exception:
            pass

        if finish_start < day_end:
            add_programme(
                tv,
                tvg_id,
                finish_start,
                day_end,
                info.get("finish_title") or f"🏁 {venue} 本日開催終了",
                f"{venue}の本日のボートレースは終了しました。",
            )

    print("ボートレース: 24場を当日JSONから生成")



def build_jra_epg(tv, date_str, data):
    """JRA EAST/WEST/HOKKAIDO + グリーンチャンネル公式番組表。"""
    day_start, day_end = day_bounds(date_str)

    if data.get("date") != date_str:
        for key, tvg_id in JRA_CHANNEL_MAP.items():
            add_programme(
                tv, tvg_id, day_start, day_end,
                f"⚠️ {key.upper()} 当日データ未取得",
                "中央競馬の当日JSONがありません。",
            )
        return

    venues = data.get("venues", {})
    channel_venues = data.get("channels", {})

    # EAST / WEST / HOKKAIDO
    for channel_key in ("east", "west", "hokkaido"):
        tvg_id = JRA_CHANNEL_MAP[channel_key]
        names = channel_venues.get(channel_key, [])

        if not names:
            add_programme(
                tv, tvg_id, day_start, day_end,
                "💤 本日非開催 JRA " + channel_key.upper(),
                f"🏇 本日はJRA {channel_key.upper()}対象競馬場の開催はありません。",
            )
            continue

        races = []
        for venue in names:
            info = venues.get(venue, {})
            for race in info.get("races", []):
                try:
                    dt = parse_hm(date_str, race.get("time", ""))
                    races.append((venue, race, dt))
                except Exception:
                    pass

        races.sort(key=lambda x: x[2])
        if not races:
            add_programme(
                tv, tvg_id, day_start, day_end,
                f"📅 JRA {channel_key.upper()} 開催予定",
                "JRA公式で開催は確認しましたが発走時刻を取得できませんでした。",
            )
            continue

        pre_start = max(day_start, races[0][2] - datetime.timedelta(minutes=20))
        if day_start < pre_start:
            venue, race, _ = races[0]
            add_programme(
                tv, tvg_id, day_start, pre_start,
                f"⏳ 待機 JRA {channel_key.upper()} {venue} 1R {race.get('time','')}",
                f"🏇 中央競馬 {venue}\n1R発走予定 {race.get('time','')}",
            )

        for i, (venue, race, start_time) in enumerate(races):
            block_start = max(pre_start, start_time - datetime.timedelta(minutes=8))

            if i + 1 < len(races):
                block_stop = races[i+1][2] - datetime.timedelta(minutes=8)
            else:
                block_stop = start_time + datetime.timedelta(minutes=30)

            if block_stop <= block_start:
                block_stop = start_time + datetime.timedelta(minutes=12)

            race_no = race.get("race", "")
            race_time = race.get("time", "")
            race_name = clean_text(race.get("name", "")) or "競走"
            race_type = clean_text(race.get("race_type", ""))
            icon = clean_text(race.get("icon", "")) or "🐎"
            main = bool(race.get("main"))

            title_parts = []
            if main:
                title_parts.append("🏆 MAIN")
            title_parts += [icon, f"{venue} {race_no}R", f"{race_time}発走", race_name]
            if race_type and race_type not in {"一般", race_name} and race_type not in race_name:
                title_parts.append(f"【{race_type}】")

            desc = [
                f"🏇 JRA {channel_key.upper()} / {venue}",
                f"⏰ 発走予定: {race_time}",
                f"📢 レース名: {race_name}",
            ]
            conditions = clean_text(race.get("conditions", ""))
            if conditions and conditions != race_name:
                desc.append(f"📋 条件: {conditions}")
            if main:
                desc.append("🏆 メインレース")

            add_programme(
                tv, tvg_id, block_start, min(block_stop, day_end),
                " ".join(title_parts), "\n".join(desc),
            )

        finish = races[-1][2] + datetime.timedelta(minutes=30)
        if finish < day_end:
            add_programme(
                tv, tvg_id, finish, day_end,
                f"🏁 JRA {channel_key.upper()} 本日開催終了",
                "本日の中央競馬中継対象レースは終了しました。",
            )

    # グリーンチャンネル本放送：公式番組表を優先
    gch = data.get("greenchannel", {})
    programs = gch.get("programs", []) if gch.get("ok") else []
    tvg_id = JRA_CHANNEL_MAP["gch"]

    if not programs:
        add_programme(
            tv, tvg_id, day_start, day_end,
            "📺 グリーンチャンネル",
            "グリーンチャンネル公式番組表を取得できなかったため、番組名は次回更新時に再取得します。",
        )
    else:
        valid = []
        for p in programs:
            try:
                start = parse_hm(date_str, p["start"])
                stop = parse_hm(date_str, p["stop"])
                if stop <= start:
                    stop += datetime.timedelta(days=1)
                valid.append((start, stop, p))
            except Exception:
                pass

        valid.sort(key=lambda x: x[0])
        if valid and day_start < valid[0][0]:
            add_programme(tv, tvg_id, day_start, valid[0][0], "📺 グリーンチャンネル")

        for start, stop, p in valid:
            add_programme(
                tv, tvg_id,
                max(start, day_start), min(stop, day_end),
                f"📺 {clean_text(p.get('title','')) or 'グリーンチャンネル'}",
                "グリーンチャンネル公式番組表",
            )

        if valid and valid[-1][1] < day_end:
            add_programme(tv, tvg_id, valid[-1][1], day_end, "📺 グリーンチャンネル")

    print(
        "中央競馬EPG:",
        "EAST=" + ",".join(channel_venues.get("east", [])),
        "WEST=" + ",".join(channel_venues.get("west", [])),
        "HOKKAIDO=" + ",".join(channel_venues.get("hokkaido", [])),
        "GCH=" + ("公式番組表" if programs else "プレースホルダー"),
    )


def build_epg():
    today = datetime.datetime.now(JST)
    date_str = today.strftime("%Y%m%d")

    keirin = load_json(KEIRIN_JSON)
    keiba = load_json(KEIBA_JSON)
    autorace = load_json(AUTORACE_JSON)
    boat = load_json(BOAT_JSON)
    jra = load_json(JRA_JSON)

    tv = ET.Element("tv", {"generator-info-name": "PublicSportsIPTV"})

    all_maps = (KEIRIN_MAP, KEIBA_MAP, AUTO_MAP, BOAT_MAP)
    seen = set()
    for venue_map in all_maps:
        for venue, tvg_id in venue_map.items():
            if tvg_id in seen:
                continue
            seen.add(tvg_id)
            ch = ET.SubElement(tv, "channel", id=tvg_id)
            ET.SubElement(ch, "display-name").text = venue

    jra_display = {
        "jra.gch": "グリーンチャンネル",
        "jra.east": "JRA EAST",
        "jra.west": "JRA WEST",
        "jra.hokkaido": "JRA HOKKAIDO",
    }
    for tvg_id, name in jra_display.items():
        ch = ET.SubElement(tv, "channel", id=tvg_id)
        ET.SubElement(ch, "display-name").text = name

    build_standard_race_epg(
        tv, date_str, keirin, KEIRIN_MAP, "競輪", "🚲"
    )
    build_standard_race_epg(
        tv, date_str, keiba, KEIBA_MAP, "地方競馬", "🐎"
    )
    build_standard_race_epg(
        tv, date_str, autorace, AUTO_MAP, "オートレース", "🏍️"
    )
    build_boat_epg(tv, date_str, boat)
    build_jra_epg(tv, date_str, jra)

    tree = ET.ElementTree(tv)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="    ")

    tree.write(
        OUT_XML,
        encoding="utf-8",
        xml_declaration=True,
    )

    programme_count = len(tv.findall("programme"))
    channel_count = len(tv.findall("channel"))

    print("")
    print("============================")
    print("EPG生成完了")
    print(f"日付: {date_str}")
    print(f"チャンネル数: {channel_count}")
    print(f"番組数: {programme_count}")
    print(f"出力: {OUT_XML}")
    print("============================")


if __name__ == "__main__":
    build_epg()
