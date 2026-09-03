from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

JST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(JST)
TODAY = NOW.date()
JSON_PATH = Path("boatrace_today.json")
BOAT_M3U = Path("boatrace_today.m3u")
PUBLIC_M3U = Path("public_sports.m3u")

TVG_RE = re.compile(r'tvg-id="([^"]+)"', re.I)


def parse_hhmm(value: str | None, reference: dt.datetime | None = None) -> dt.datetime | None:
    if not value:
        return None
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(value).strip())
    if not m:
        return None
    hour, minute = map(int, m.groups())
    if hour < 0 or not 0 <= minute < 60:
        return None
    day_offset, clock_hour = divmod(hour, 24)
    base = dt.datetime.combine(TODAY + dt.timedelta(days=day_offset), dt.time(clock_hour, minute), tzinfo=JST)
    if reference is not None:
        while base < reference:
            base += dt.timedelta(days=1)
    return base


def finish_time(item: dict) -> dt.datetime | None:
    # Stream end values can cross midnight (for example 01:59 means the next day).
    start = parse_hhmm(item.get("start"))
    end = parse_hhmm(item.get("end"), reference=start)
    if end:
        return end

    # Fall back to explicit EPG finish_end if available, but reject stale dates.
    finish_end = item.get("finish_end")
    if finish_end:
        try:
            parsed = dt.datetime.strptime(finish_end, "%Y-%m-%d %H:%M").replace(tzinfo=JST)
            if parsed.date() >= TODAY:
                return parsed
        except Exception:
            pass

    # Final fallback: 15 minutes after the last race deadline, respecting midnight rollover.
    races = item.get("races") or []
    times = [parse_hhmm(r.get("time"), reference=start) for r in races if isinstance(r, dict)]
    times = [x for x in times if x is not None]
    if times:
        return max(times) + dt.timedelta(minutes=15)
    return None


def parse_entries(text: str) -> tuple[list[str], dict[str, list[str]]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    header: list[str] = []
    entries: dict[str, list[str]] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:"):
            block = [line]
            m = TVG_RE.search(line)
            tvg = m.group(1).strip() if m else ""
            i += 1
            while i < len(lines) and not lines[i].startswith("#EXTINF:"):
                if lines[i].startswith("## "):
                    break
                block.append(lines[i])
                i += 1
            while block and block[-1] == "":
                block.pop()
            if tvg:
                entries[tvg] = block
            continue
        header.append(line)
        i += 1
    return header, entries


def write_boat_m3u(entries: dict[str, list[str]], keep_ids: set[str]) -> None:
    out = ["#EXTM3U", ""]
    kept = 0
    for tvg, block in entries.items():
        if tvg not in keep_ids:
            continue
        out.extend(block)
        out.append("")
        kept += 1
    BOAT_M3U.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"BOAT prune: kept={kept} removed={len(entries) - kept}")


def replace_public_boat_section(boat_text: str) -> None:
    if not PUBLIC_M3U.exists():
        return
    public = PUBLIC_M3U.read_text(encoding="utf-8-sig")
    boat_lines = boat_text.replace("\r\n", "\n").split("\n")
    boat_payload = [x for x in boat_lines if x.strip() and not x.startswith("#EXTM3U")]
    replacement = "## ボートレース\n"
    if boat_payload:
        replacement += "\n".join(boat_payload).rstrip() + "\n"

    pat = re.compile(r"(?ms)^## ボートレース\n.*?(?=^## |\Z)")
    if pat.search(public):
        public = pat.sub(replacement, public)
    else:
        public = public.rstrip() + "\n\n" + replacement
    PUBLIC_M3U.write_text(public.rstrip() + "\n", encoding="utf-8")
    print("BOAT prune: public_sports.m3u synchronized")


def main() -> None:
    if not JSON_PATH.exists() or not BOAT_M3U.exists():
        raise SystemExit("BOAT prune: required files missing")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8-sig"))
    _, entries = parse_entries(BOAT_M3U.read_text(encoding="utf-8-sig"))

    keep_ids: set[str] = set()
    for venue, item in data.items():
        if not isinstance(item, dict) or item.get("held") is not True:
            continue
        tvg = str(item.get("tvg_id") or "").strip()
        if not tvg or tvg not in entries:
            continue
        end = finish_time(item)
        if end is not None and NOW >= end:
            item["live"] = False
            item.pop("url", None)
            print(f"BOAT finished -> remove: {venue} ({tvg}) end={end:%m-%d %H:%M}")
            continue
        keep_ids.add(tvg)

    write_boat_m3u(entries, keep_ids)
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    replace_public_boat_section(BOAT_M3U.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
