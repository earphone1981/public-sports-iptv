#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html as html_lib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

JST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(JST)
TODAY = NOW.date()
DATE8 = NOW.strftime("%Y%m%d")
DATE10 = NOW.strftime("%Y-%m-%d")
ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "boatrace_today.json"
M3U_PATH = ROOT / "boatrace_today.m3u"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
PLAYER_HEADERS = {
    "Origin": "https://front.player.boatrace-cdn.jp",
    "Referer": "https://front.player.boatrace-cdn.jp/",
    "User-Agent": UA,
}
WEB_HEADERS = {"User-Agent": UA}

VENUES = [
    ("01 桐生", "01", "01kiryu", "boat.kiryu", "https://www.boatrace.jp/static/uploads/sites/8/01_N.jpg"),
    ("02 戸田", "02", "02toda", "boat.toda", "https://www.boatrace.jp/static/uploads/sites/8/02_N-1.jpg"),
    ("03 江戸川", "03", "03edogawa", "boat.edogawa", "https://www.boatrace.jp/static/uploads/sites/8/03_N-1.jpg"),
    ("04 平和島", "04", "04heiwajima", "boat.heiwajima", "https://www.boatrace.jp/static/uploads/sites/8/04_N-1.jpg"),
    ("05 多摩川", "05", "05tamagawa", "boat.tamagawa", "https://www.boatrace.jp/static/uploads/sites/8/05_N-1.jpg"),
    ("06 浜名湖", "06", "06hamanako", "boat.hamanako", "https://www.boatrace.jp/static/uploads/sites/8/06_N-1.jpg"),
    ("07 蒲郡", "07", "07gamagori", "boat.gamagori", "https://www.boatrace.jp/static/uploads/sites/8/07_N-1.jpg"),
    ("08 常滑", "08", "08tokoname", "boat.tokoname", "https://www.boatrace.jp/static/uploads/sites/8/08_N-1.jpg"),
    ("09 津", "09", "09tsu", "boat.tsu", "https://www.boatrace.jp/static/uploads/sites/8/09_N-1-1.jpg"),
    ("10 三国", "10", "10mikuni", "boat.mikuni", "https://www.boatrace.jp/static/uploads/sites/8/10_N-1-1.jpg"),
    ("11 びわこ", "11", "11biwako", "boat.biwako", "https://www.boatrace.jp/static/uploads/sites/8/11_N-1.jpg"),
    ("12 住之江", "12", "12suminoe", "boat.suminoe", "https://www.boatrace.jp/static/uploads/sites/8/12_N-1-1.jpg"),
    ("13 尼崎", "13", "13amagasaki", "boat.amagasaki", "https://www.boatrace.jp/static/uploads/sites/8/13_N-1.jpg"),
    ("14 鳴門", "14", "14naruto", "boat.naruto", "https://www.boatrace.jp/static/uploads/sites/8/14_N-1.jpg"),
    ("15 丸亀", "15", "15marugame", "boat.marugame", "https://www.boatrace.jp/static/uploads/sites/8/15_N-1.jpg"),
    ("16 児島", "16", "16kojima", "boat.kojima", "https://www.boatrace.jp/static/uploads/sites/8/16_N-1.jpg"),
    ("17 宮島", "17", "17miyajima", "boat.miyajima", "https://www.boatrace.jp/static/uploads/sites/8/17_N-1.jpg"),
    ("18 徳山", "18", "18tokuyama", "boat.tokuyama", "https://www.boatrace.jp/static/uploads/sites/8/18_N-1.jpg"),
    ("19 下関", "19", "19shimonoseki", "boat.shimonoseki", "https://www.boatrace.jp/static/uploads/sites/8/19_N-1.jpg"),
    ("20 若松", "20", "20wakamatsu", "boat.wakamatsu", "https://www.boatrace.jp/static/uploads/sites/8/20_N-1.jpg"),
    ("21 芦屋", "21", "21ashiya", "boat.ashiya", "https://www.boatrace.jp/static/uploads/sites/8/21_N-1.jpg"),
    ("22 福岡", "22", "22fukuoka", "boat.fukuoka", "https://www.boatrace.jp/static/uploads/sites/8/22_N-1-1.jpg"),
    ("23 唐津", "23", "23karatsu", "boat.karatsu", "https://www.boatrace.jp/static/uploads/sites/8/23_N-1.jpg"),
    ("24 大村", "24", "24omura", "boat.omura", "https://www.boatrace.jp/static/uploads/sites/8/24_N-1.jpg"),
]


def fetch_text(url: str, headers: dict[str, str], timeout: int = 6) -> str:
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def html_to_text(raw: str) -> str:
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html_lib.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def parse_iso(value: str | None):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(JST)
    except Exception:
        return None


def get_setting(code: str):
    url = f"https://front.player.boatrace-cdn.jp/setting/live/{code}/setting.json?t={int(time.time())}"
    try:
        obj = json.loads(fetch_text(url, PLAYER_HEADERS))
        live = obj.get("br_live") or {}
        return parse_iso(live.get("start_at")), parse_iso(live.get("end_at"))
    except Exception:
        return None, None


def get_race_times(jcd: str):
    url = f"https://www.boatrace.jp/owpc/pc/race/raceindex?hd={DATE8}&jcd={jcd}"
    try:
        text = html_to_text(fetch_text(url, WEB_HEADERS))
    except Exception:
        return {}
    out = {}
    for m in re.finditer(r"(?<!\d)(1[0-2]|[1-9])R\s+([0-2][0-9]:[0-5][0-9])", text):
        rno = int(m.group(1))
        out.setdefault(rno, m.group(2))
    return out


def normalized_race_datetimes(race_times: dict[int, str]):
    out = {}
    prev = None
    for rno in sorted(race_times):
        h, m = map(int, race_times[rno].split(":"))
        cur = dt.datetime.combine(TODAY, dt.time(h, m), JST)
        if prev is not None and cur < prev - dt.timedelta(hours=6):
            cur += dt.timedelta(days=1)
        out[rno] = cur
        prev = cur
    return out


def in_live_window(race_dts: dict[int, dt.datetime]):
    if not race_dts:
        return False
    first = race_dts[min(race_dts)]
    last = race_dts[max(race_dts)]
    now = NOW
    if first.hour >= 18 and now.hour < 6 and now.date() == TODAY + dt.timedelta(days=1):
        pass
    return first - dt.timedelta(minutes=60) <= now <= last + dt.timedelta(minutes=45)


def get_playback(code: str):
    url = (
        "https://playback.api.streaks.jp/v1/projects/cp-boatrace-prod/medias/"
        f"ref:lm-br-{code}-tokyo-{DATE8}?audio_only=false"
    )
    try:
        obj = json.loads(fetch_text(url, PLAYER_HEADERS))
        sources = obj.get("sources") or []
        if sources and sources[0].get("src"):
            return sources[0]["src"]
    except Exception:
        pass
    return None


def old_race_names():
    if not JSON_PATH.exists():
        return {}
    try:
        data = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    out = {}
    for venue, item in data.items():
        for race in item.get("races") or []:
            if str(race.get("epg_start") or "").startswith(DATE10):
                out[(venue, int(race.get("rno") or 0))] = str(race.get("race_name") or "")
    return out


def day_type(start, end):
    if not start or not end:
        return "", "🚤"
    end_cmp = end
    if end_cmp.date() > start.date() or end_cmp.hour < start.hour:
        return "ミッドナイト", "🌟"
    mins = end.hour * 60 + end.minute
    if mins >= 20 * 60:
        return "ナイター", "🌙"
    if start.hour * 60 + start.minute < 9 * 60:
        return "モーニング", "🌅"
    if mins >= 18 * 60:
        return "サマータイム", "🌇"
    return "デイ", "🌞"


def scan_venue(v):
    name, jcd, code, tvg_id, logo = v
    race_times = get_race_times(jcd)
    held = bool(race_times)
    start, end = get_setting(code)
    race_dts = normalized_race_datetimes(race_times)
    stream = get_playback(code) if held and in_live_window(race_dts) else None
    return {
        "name": name, "jcd": jcd, "code": code, "tvg_id": tvg_id, "logo": logo,
        "race_times": race_times, "race_dts": race_dts, "held": held,
        "start": start, "end": end, "stream": stream,
    }


def fmt(x: dt.datetime):
    return x.strftime("%Y-%m-%d %H:%M")


def main():
    old_names = old_race_names()
    scanned = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(scan_venue, v): v for v in VENUES}
        for fut in as_completed(futures):
            v = futures[fut]
            try:
                row = fut.result()
            except Exception as e:
                name, jcd, code, tvg_id, logo = v
                print(f"BOAT scan failed {name}: {type(e).__name__}: {e}")
                row = {"name": name, "jcd": jcd, "code": code, "tvg_id": tvg_id, "logo": logo,
                       "race_times": {}, "race_dts": {}, "held": False, "start": None, "end": None, "stream": None}
            scanned[row["tvg_id"]] = row

    today_data = {}
    m3u = ["#EXTM3U", ""]
    live_count = 0
    held_count = 0

    for name, jcd, code, tvg_id, logo in VENUES:
        row = scanned[tvg_id]
        held = row["held"]
        stream = row["stream"]
        start = row["start"]
        end = row["end"]
        dtype, emoji = day_type(start, end)
        item = {
            "tvg_id": tvg_id,
            "logo": logo,
            "live": bool(stream),
            "held": held,
            "day_type": dtype,
            "emoji": emoji,
            "races": [],
        }
        if start:
            item["start"] = start.strftime("%H:%M")
        if end:
            item["end"] = end.strftime("%H:%M")
        if stream:
            item["url"] = stream
            m3u += [
                f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="ボートレース",{name}',
                stream,
                "",
            ]
            live_count += 1

        if not held:
            item["status_title"] = f"⛔ {name} 本日非開催"
            today_data[name] = item
            print(f"BOAT {name}: non-event")
            continue

        held_count += 1
        race_dts = row["race_dts"]
        prev = None
        for rno in sorted(row["race_times"]):
            deadline = row["race_times"][rno]
            end_dt = race_dts[rno]
            if prev is None:
                epg_start = start if start and start <= end_dt else end_dt - dt.timedelta(minutes=30)
            else:
                epg_start = prev
            race_name = old_names.get((name, rno), "")
            title = f"{emoji} {name} {rno}R"
            if race_name:
                title += f" {race_name}"
            title += f"【{deadline}】"
            item["races"].append({
                "rno": rno,
                "time": deadline,
                "race_name": race_name,
                "title": title,
                "epg_start": fmt(epg_start),
                "epg_end": fmt(end_dt),
            })
            prev = end_dt

        if prev:
            item["finish_title"] = f"🏁 {name} 本日開催終了"
            item["finish_start"] = fmt(prev)
            finish_end = end if end and end > prev else prev + dt.timedelta(hours=2)
            item["finish_end"] = fmt(finish_end)

        today_data[name] = item
        status = "Streaks OK" if stream else "held / direct stream unavailable"
        print(f"BOAT {name}: {status}; races={len(item['races'])}")

    M3U_PATH.write_text("\n".join(m3u).rstrip() + "\n", encoding="utf-8")
    JSON_PATH.write_text(json.dumps(today_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"BOAT fast update complete: held={held_count} direct_live={live_count} date={DATE8}")


if __name__ == "__main__":
    main()
