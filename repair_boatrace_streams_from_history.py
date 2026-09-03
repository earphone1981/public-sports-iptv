import base64
import datetime as dt
import html as html_lib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import Request, urlopen

JST = dt.timezone(dt.timedelta(hours=9))
NOW_UTC = dt.datetime.now(dt.timezone.utc)
NOW_JST = NOW_UTC.astimezone(JST)
TODAY_JST = NOW_JST.date()
DATE8 = NOW_JST.strftime("%Y%m%d")
JSON_PATH = Path("boatrace_today.json")
M3U_PATH = Path("boatrace_today.m3u")
COOKIES = Path("youtube_cookies.txt")
UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/151 Mobile Safari/537.36"
STREAKS_HEADERS = {
    "Accept": "application/json",
    "Origin": "https://players.streaks.jp",
    "Referer": "https://players.streaks.jp/",
    "User-Agent": UA,
}
JLC_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/javascript,*/*;q=0.8",
    "Referer": "https://livebb.jlc.ne.jp/",
    "User-Agent": UA,
}

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
VENUE_CODES = {
    "boat.kiryu": "01kiryu", "boat.toda": "02toda", "boat.edogawa": "03edogawa",
    "boat.heiwajima": "04heiwajima", "boat.tamagawa": "05tamagawa", "boat.hamanako": "06hamanako",
    "boat.gamagori": "07gamagori", "boat.tokoname": "08tokoname", "boat.tsu": "09tsu",
    "boat.mikuni": "10mikuni", "boat.biwako": "11biwako", "boat.suminoe": "12suminoe",
    "boat.amagasaki": "13amagasaki", "boat.naruto": "14naruto", "boat.marugame": "15marugame",
    "boat.kojima": "16kojima", "boat.miyajima": "17miyajima", "boat.tokuyama": "18tokuyama",
    "boat.shimonoseki": "19shimonoseki", "boat.wakamatsu": "20wakamatsu", "boat.ashiya": "21ashiya",
    "boat.fukuoka": "22fukuoka", "boat.karatsu": "23karatsu", "boat.omura": "24omura",
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
        start = payload.get("start") or payload.get("nbf") or payload.get("iat")
        if start:
            start_day = dt.datetime.fromtimestamp(int(start), dt.timezone.utc).astimezone(JST).date()
            if start_day != TODAY_JST:
                return False
        return True
    except Exception:
        return False


def fetch_text(url: str, headers: dict, timeout: int = 8):
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace"), r.geturl()


def fetch_streaks_hls(tvg: str):
    code = VENUE_CODES.get(tvg)
    if not code:
        return None
    api = (
        "https://playback.api.streaks.jp/v1/projects/cp-boatrace-prod/medias/"
        f"ref:lm-br-{code}-tokyo-{DATE8}?audio_only=false"
    )
    try:
        text, _ = fetch_text(api, STREAKS_HEADERS)
        obj = json.loads(text)
        for src in obj.get("sources") or []:
            url = str(src.get("src") or "")
            if current_streaks_url(url):
                return url
    except Exception as e:
        print(f"BOAT Streaks API failed: {tvg}: {type(e).__name__}: {e}")
    return None


def normalize_scan_text(text: str):
    return html_lib.unescape(text).replace("\\/", "/").replace("\\u0026", "&")


def m3u8_candidates(text: str, base: str):
    text = normalize_scan_text(text)
    out = []
    patterns = [
        r'https?://[^\s"\'<>]+?\.m3u8(?:\?[^\s"\'<>]*)?',
        r'//[^\s"\'<>]+?\.m3u8(?:\?[^\s"\'<>]*)?',
        r'["\']([^"\']+?\.m3u8(?:\?[^"\']*)?)["\']',
    ]
    for idx, pat in enumerate(patterns):
        for m in re.finditer(pat, text, flags=re.I):
            raw = m.group(1) if idx == 2 else m.group(0)
            if raw.startswith("//"):
                raw = "https:" + raw
            elif not raw.startswith(("http://", "https://")):
                raw = urljoin(base, raw)
            raw = raw.rstrip("\\);,]")
            if raw not in out:
                out.append(raw)
    return out


def linked_assets(text: str, base: str):
    text = normalize_scan_text(text)
    out = []
    for m in re.finditer(r'(?:src|href)\s*=\s*["\']([^"\']+)["\']', text, flags=re.I):
        u = urljoin(base, m.group(1))
        if not u.startswith("http"):
            continue
        host = (urlsplit(u).hostname or "").lower()
        path = urlsplit(u).path.lower()
        if host.endswith("jlc.ne.jp") and (path.endswith(".js") or "streamer" in path or "live_" in path):
            if u not in out:
                out.append(u)
    for m in re.finditer(r'["\']([^"\']+(?:\.js|streamer\.php)[^"\']*)["\']', text, flags=re.I):
        u = urljoin(base, m.group(1))
        host = (urlsplit(u).hostname or "").lower()
        if host.endswith("jlc.ne.jp") and u not in out:
            out.append(u)
    return out


def fetch_jlc_hls(tvg: str):
    code = VENUE_CODES.get(tvg)
    if not code:
        return None
    jo = code[:2]
    queue = [
        f"https://livebb.jlc.ne.jp/bb_top/sp_bb/live_{jo}.php",
        f"https://livebb.jlc.ne.jp/bb_top/new_bb/streamer/streamer.php?jo={jo}&md=L",
        f"https://livebb.jlc.ne.jp/bb_top/sp_bb/streamer/streamer.php?jo={jo}&m=1",
    ]
    seen = set()
    while queue and len(seen) < 16:
        u = queue.pop(0)
        if u in seen:
            continue
        seen.add(u)
        try:
            text, final_url = fetch_text(u, JLC_HEADERS, timeout=7)
        except Exception as e:
            print(f"BOAT JLC fetch failed: {tvg}: {type(e).__name__}: {e}")
            continue
        found = m3u8_candidates(text, final_url)
        if found:
            preferred = [x for x in found if "vod" not in x.lower() and "replay" not in x.lower()]
            url = (preferred or found)[0]
            print(f"BOAT JLC m3u8 discovered: {tvg}: {url}")
            return url
        for asset in linked_assets(text, final_url):
            if asset not in seen and asset not in queue:
                queue.append(asset)
    return None


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
    return (first - 50) <= now <= (last + 45)


def ytdlp_base():
    cmd = ["yt-dlp", "--no-warnings", "--no-cache-dir"]
    if COOKIES.exists() and COOKIES.stat().st_size > 20:
        cmd += ["--cookies", str(COOKIES)]
    cmd += ["--js-runtimes", "node"]
    return cmd


def extract_live_hls(name: str):
    queries = [
        f"ytsearch5:BOATRACE {name} 公式 レースライブ",
        f"ytsearch5:ボートレース{name} レースライブ",
    ]
    errors = []
    for query in queries:
        try:
            p = subprocess.run(
                ytdlp_base() + [
                    "--extractor-args", "youtube:player_client=default,web_safari,web",
                    "--no-playlist",
                    "--match-filter", "is_live",
                    "-f", "best[protocol^=m3u8]/best",
                    "-g", query,
                ],
                text=True,
                capture_output=True,
                timeout=40,
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


def resolve_one(tvg: str, venue: str, item: dict):
    jlc = fetch_jlc_hls(tvg)
    if jlc:
        return tvg, VENUE_NAMES.get(tvg) or venue, jlc, "jlc", None
    official = fetch_streaks_hls(tvg)
    if official:
        return tvg, VENUE_NAMES.get(tvg) or venue, official, "streaks", None
    name = VENUE_NAMES.get(tvg) or re.sub(r"^\d+\s*", "", venue)
    try:
        return tvg, name, extract_live_hls(name), "youtube", None
    except Exception as e:
        return tvg, name, None, None, f"{type(e).__name__}: {e}"


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

    for tvg, entry in current.items():
        if tvg in held and current_streaks_url(entry[1]):
            chosen[tvg] = entry
            print(f"BOAT primary current-day Streaks: {tvg}")
        elif tvg in held and "googlevideo.com" not in entry[1]:
            chosen[tvg] = entry
            print(f"BOAT retained non-Google public HLS: {tvg}")
        elif tvg in held:
            print(f"BOAT rejected IP-bound/stale primary URL: {tvg}")

    targets = []
    for tvg, (venue, item) in held.items():
        if tvg in chosen:
            continue
        if not in_live_window(item):
            item["live"] = False
            item.pop("url", None)
            print(f"BOAT live fallback skip outside live window: {tvg} {venue}")
            continue
        targets.append((tvg, venue, item))

    jlc_ok = 0
    streaks_ok = 0
    youtube_ok = 0
    fallback_fail = 0
    if targets:
        print(f"BOAT live resolve parallel targets={len(targets)} workers={min(4, len(targets))}")
        with ThreadPoolExecutor(max_workers=min(4, len(targets))) as ex:
            futures = {ex.submit(resolve_one, tvg, venue, item): (tvg, venue, item) for tvg, venue, item in targets}
            for fut in as_completed(futures):
                tvg, venue, item = futures[fut]
                rtvg, name, url, source, error = fut.result()
                if url:
                    chosen[rtvg] = ("", url)
                    if source == "jlc":
                        jlc_ok += 1
                        print(f"BOAT JLC public HLS OK: {rtvg} {name}")
                    elif source == "streaks":
                        streaks_ok += 1
                        print(f"BOAT Streaks official HLS OK: {rtvg} {name}")
                    else:
                        youtube_ok += 1
                        print(f"BOAT YouTube LIVE fallback OK: {rtvg} {name}")
                else:
                    fallback_fail += 1
                    item["live"] = False
                    item.pop("url", None)
                    print(f"BOAT live resolve failed: {rtvg} {name}: {error}")

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
        f"BOAT current-live result: held={len(held)} live={live_count} "
        f"jlc_ok={jlc_ok} streaks_ok={streaks_ok} youtube_ok={youtube_ok} fail={fallback_fail}; history disabled"
    )


if __name__ == "__main__":
    main()
