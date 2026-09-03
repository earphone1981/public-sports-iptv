import base64
import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

JST = dt.timezone(dt.timedelta(hours=9))
NOW_UTC = dt.datetime.now(dt.timezone.utc)
NOW_JST = NOW_UTC.astimezone(JST)
TODAY_JST = NOW_JST.date()
JSON_PATH = Path("boatrace_today.json")
M3U_PATH = Path("boatrace_today.m3u")
COOKIES = Path("youtube_cookies.txt")

VENUE_NAMES = {
    "boat.kiryu": "桐生", "boat.toda": "戸田", "boat.edogawa": "江戸川",
    "boat.heiwajima": "平和島", "boat.tamagawa": "多摩川", "boat.hamanako": "浜名湖",
    "boat.gamagori": "蒲郡", "boat.tokoname": "常滑", "boat.tsu": "津",
    "boat.mikuni": "三国", "boat.biwako": "びわこ", "boat.suminoe": "住之江",
    "boat.amagasaki": "尼崎", "boat.naruto": "鳴門", "boat.marugame": "丸亀",
    "boat.kojima": "児島", "boat.miyajima": "宮島", "boat.tokuyama": "徳山",
    "boat.shimonoseki": "下関", "boat.wakamatsu": "若松", "boat.ashiya": "芦屋",
    "boat.fukuoka": "福岡", "boat.karatsu": "唐津", "boat.omura": "大村",
}


def jwt_payload(url: str):
    m = re.search(r"[?&]token=([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)", url)
    if not m:
        return None
    try:
        payload = m.group(2)
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except Exception:
        return None


def current_streaks_url(url: str) -> bool:
    if "manifest.streaks.jp" not in url:
        return False
    payload = jwt_payload(url)
    if not payload:
        return False
    try:
        exp = int(payload.get("exp") or 0)
        if exp <= int(NOW_UTC.timestamp()) + 600:
            return False
        # The old recovery code accepted any unexpired JWT.  BOAT tokens can
        # remain unexpired after the actual broadcast day, which restored a
        # previous-day VTR as if it were today's live feed.  Require the media
        # start date to be today in JST when the token exposes start/nbf/iat.
        start = payload.get("start") or payload.get("nbf") or payload.get("iat")
        if start:
            start_day = dt.datetime.fromtimestamp(int(start), dt.timezone.utc).astimezone(JST).date()
            if start_day != TODAY_JST:
                return False
        return True
    except Exception:
        return False


def youtube_url_fresh(url: str) -> bool:
    try:
        q = parse_qs(urlsplit(url).query)
        expire = (q.get("expire") or [None])[0]
        if expire and int(expire) <= int(NOW_UTC.timestamp()) + 300:
            return False
    except Exception:
        pass
    return "googlevideo.com" in url or "youtube.com" in url or "youtu.be" in url


def parse_entries(text: str):
    lines = text.replace("\r\n", "\n").split("\n")
    out = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            m = re.search(r'tvg-id="([^"]+)"', line)
            tvg = m.group(1) if m else None
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].lstrip().startswith("#")):
                j += 1
            if tvg and j < len(lines):
                url = lines[j].strip()
                if url.startswith("http"):
                    out[tvg] = (line, url)
            i = j
        i += 1
    return out


def time_minutes(text: str):
    try:
        h, m = map(int, text.split(":", 1))
        return h * 60 + m
    except Exception:
        return None


def in_live_window(item: dict) -> bool:
    races = item.get("races") or []
    times = [time_minutes(str(r.get("time") or "")) for r in races]
    times = [x for x in times if x is not None]
    if not times:
        return bool(item.get("held"))
    first = times[0]
    normalized = [first]
    for x in times[1:]:
        if x < normalized[-1] - 360:
            x += 1440
        normalized.append(x)
    last = normalized[-1]
    now = NOW_JST.hour * 60 + NOW_JST.minute
    if first >= 18 * 60 and now < 6 * 60:
        now += 1440
    # Resolve shortly before 1R and keep trying until 45 min after the final deadline.
    return (first - 50) <= now <= (last + 45)


def ytdlp_base():
    cmd = ["yt-dlp", "--no-warnings", "--no-cache-dir"]
    if COOKIES.exists() and COOKIES.stat().st_size > 20:
        cmd += ["--cookies", str(COOKIES)]
    # Current yt-dlp can use Node on GitHub-hosted runners for YouTube JS challenges.
    cmd += ["--js-runtimes", "node"]
    return cmd


def extract_live_hls(name: str):
    queries = [
        f"ytsearch5:BOATRACE {name} 公式 レースライブ",
        f"ytsearch5:ボートレース{name} レースライブ",
        f"ytsearch5:{name} ボートレース LIVE 公式",
    ]
    errors = []
    for query in queries:
        for selector in ("best[protocol^=m3u8]", "best"):
            try:
                p = subprocess.run(
                    ytdlp_base() + [
                        "--extractor-args", "youtube:player_client=default,web_safari,web",
                        "--no-playlist",
                        "--match-filter", "is_live",
                        "-f", selector,
                        "-g", query,
                    ],
                    text=True,
                    capture_output=True,
                    timeout=50,
                )
            except subprocess.TimeoutExpired:
                errors.append("timeout")
                continue
            urls = [x.strip() for x in p.stdout.splitlines() if x.strip().startswith(("http://", "https://"))]
            for url in urls:
                if (".m3u8" in url or "manifest.googlevideo.com" in url) and youtube_url_fresh(url):
                    return url
            msg = (p.stderr or p.stdout or f"yt-dlp rc={p.returncode}").strip()
            if msg:
                errors.append(msg[-600:])
            low = msg.lower()
            if "429" in low or "too many requests" in low or "sign in to confirm" in low:
                break
    raise RuntimeError(" | ".join(errors)[-1000:] or "no live HLS")


def main():
    if not JSON_PATH.exists():
        print("BOAT live fallback: JSON missing")
        return

    data = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
    held = {}
    for venue, item in data.items():
        if item.get("held") is True:
            tvg = item.get("tvg_id")
            if tvg:
                held[tvg] = (venue, item)

    current_text = M3U_PATH.read_text(encoding="utf-8-sig") if M3U_PATH.exists() else "#EXTM3U\n"
    current = parse_entries(current_text)
    chosen = {}

    # Only keep a Streaks URL produced for today's JST broadcast.  Never scan git
    # history here: an old but unexpired token is exactly what caused the black screen.
    for tvg, entry in current.items():
        if tvg in held and current_streaks_url(entry[1]):
            chosen[tvg] = entry
            print(f"BOAT primary current-day Streaks: {tvg}")
        elif tvg in held:
            print(f"BOAT rejected stale/non-current primary URL: {tvg}")

    youtube_ok = 0
    youtube_fail = 0
    for tvg, (venue, item) in held.items():
        if tvg in chosen:
            continue
        if not in_live_window(item):
            item["live"] = False
            item.pop("url", None)
            print(f"BOAT live fallback skip outside live window: {tvg} {venue}")
            continue
        name = VENUE_NAMES.get(tvg) or re.sub(r"^\d+\s*", "", venue)
        try:
            url = extract_live_hls(name)
        except Exception as e:
            youtube_fail += 1
            item["live"] = False
            item.pop("url", None)
            print(f"BOAT YouTube live fallback failed: {tvg} {name}: {type(e).__name__}: {e}")
            continue
        chosen[tvg] = ("", url)
        youtube_ok += 1
        print(f"BOAT YouTube LIVE fallback OK: {tvg} {name}")

    lines = ["#EXTM3U", ""]
    live_count = 0
    for tvg, (venue, item) in held.items():
        entry = chosen.get(tvg)
        if not entry:
            item["live"] = False
            item.pop("url", None)
            continue
        _, url = entry
        logo = item.get("logo", "")
        display = venue
        extinf = (
            f'#EXTINF:-1 tvg-id="{tvg}" tvg-name="{display}" '
            f'tvg-logo="{logo}" group-title="ボートレース",{display}'
        )
        lines.extend([extinf, url, ""])
        item["live"] = True
        item["url"] = url
        live_count += 1

    M3U_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"BOAT current-live fallback result: held={len(held)} live={live_count} "
        f"youtube_ok={youtube_ok} youtube_fail={youtube_fail}; git-history restore disabled"
    )


if __name__ == "__main__":
    main()
