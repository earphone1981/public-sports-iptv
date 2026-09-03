import base64
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

JST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(dt.timezone.utc)
JSON_PATH = Path("boatrace_today.json")
M3U_PATH = Path("boatrace_today.m3u")


def git(*args):
    p = subprocess.run(["git", *args], text=True, capture_output=True)
    if p.returncode != 0:
        return ""
    return p.stdout


def jwt_exp(url: str):
    m = re.search(r"[?&]token=([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)", url)
    if not m:
        return None
    try:
        payload = m.group(2)
        payload += "=" * (-len(payload) % 4)
        obj = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        exp = obj.get("exp")
        return dt.datetime.fromtimestamp(int(exp), dt.timezone.utc) if exp else None
    except Exception:
        return None


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


def recent_versions(limit=40):
    shas = git("log", f"-n{limit}", "--format=%H", "--", "boatrace_today.m3u").splitlines()
    for sha in shas:
        text = git("show", f"{sha}:boatrace_today.m3u")
        if text:
            yield sha, parse_entries(text)


def valid_url(url: str):
    if "manifest.streaks.jp" not in url:
        return False
    exp = jwt_exp(url)
    if exp is None:
        return False
    return exp > NOW + dt.timedelta(minutes=10)


def main():
    if not JSON_PATH.exists():
        print("BOAT fallback: JSON missing")
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
        if tvg in held and valid_url(entry[1]):
            chosen[tvg] = entry

    missing = set(held) - set(chosen)
    if missing:
        for sha, entries in recent_versions():
            if not missing:
                break
            for tvg in list(missing):
                entry = entries.get(tvg)
                if not entry:
                    continue
                if valid_url(entry[1]):
                    chosen[tvg] = entry
                    missing.remove(tvg)
                    exp = jwt_exp(entry[1])
                    print(f"BOAT fallback restored {tvg} from {sha[:8]} exp={exp.isoformat() if exp else '?'}")

    lines = ["#EXTM3U", ""]
    restored = 0
    for tvg, (venue, item) in held.items():
        entry = chosen.get(tvg)
        if not entry:
            item["live"] = False
            item.pop("url", None)
            print(f"BOAT fallback unavailable: {tvg} {venue}")
            continue

        old_extinf, url = entry
        logo = item.get("logo", "")
        display = venue
        extinf = (
            f'#EXTINF:-1 tvg-id="{tvg}" tvg-name="{display}" '
            f'tvg-logo="{logo}" group-title="ボートレース",{display}'
        )
        lines.extend([extinf, url, ""])
        item["live"] = True
        item["url"] = url
        restored += 1

    M3U_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"BOAT fallback result: held={len(held)} live={restored} missing={len(missing)}")


if __name__ == "__main__":
    main()
