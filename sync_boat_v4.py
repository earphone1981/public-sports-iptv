#!/usr/bin/env python3
"""Mirror verified BOAT Auto v4 outputs from ajiousama/himitsu.

Source of truth for BOAT streams/EPG is ajiousama/himitsu. This repository
keeps its own 3-day EPG pipeline for the other sports.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://raw.githubusercontent.com/ajiousama/himitsu/main/"
UA = "public-sports-iptv BOAT-v4 mirror/1.0"


def get(name: str) -> bytes:
    req = urllib.request.Request(BASE + name, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def sync_streams() -> None:
    playlist = get("freewifi").decode("utf-8")
    status_raw = get("today_boat_status.json")
    status = json.loads(status_raw)
    if status.get("architecture_version") != 4 or not status.get("last_update_ok"):
        raise SystemExit("BOAT Auto v4 source is not healthy; refusing to replace local BOAT data")

    lines = playlist.splitlines()
    out = ["#EXTM3U", f"# BOAT-DATE:{str(status.get('date','')).replace('-', '')}", "# BOAT-SOURCE:ajiousama/himitsu BOAT Auto v4"]
    count = 0
    for i, line in enumerate(lines):
        if line.startswith("#EXTINF:") and 'tvg-id="boat.' in line:
            if i + 1 < len(lines) and lines[i + 1].startswith(("http://", "https://")):
                out += ["", line, lines[i + 1]]
                count += 1
    expected = int(status.get("visible_count", 0))
    if count < 1 or (expected and count != expected):
        raise SystemExit(f"BOAT v4 playlist mismatch: extracted={count} expected={expected}")
    Path("boatrace_today.m3u").write_text("\n".join(out) + "\n", encoding="utf-8")
    Path("boat_v4_status.json").write_bytes(status_raw)
    print(f"BOAT v4 streams synced: {count} venues; date={status.get('date')}")


def merge_epg() -> None:
    source = ET.fromstring(get("guides.xml"))
    target_path = Path("epg.xml")
    target = ET.parse(target_path).getroot()

    source_channels = {e.get("id"): e for e in source.findall("channel") if (e.get("id") or "").startswith("boat.")}
    source_programmes = [e for e in source.findall("programme") if (e.get("channel") or "").startswith("boat.")]
    if not source_channels or not source_programmes:
        raise SystemExit("BOAT v4 EPG missing in source guides.xml; refusing empty replacement")

    for e in list(target):
        if e.tag == "channel" and (e.get("id") or "").startswith("boat."):
            target.remove(e)
        elif e.tag == "programme" and (e.get("channel") or "").startswith("boat."):
            target.remove(e)

    # Channels before programmes keeps XMLTV consumers happy.
    first_programme = next((i for i, e in enumerate(list(target)) if e.tag == "programme"), len(target))
    for cid in sorted(source_channels):
        target.insert(first_programme, source_channels[cid])
        first_programme += 1
    for e in source_programmes:
        target.append(e)

    ET.ElementTree(target).write(target_path, encoding="utf-8", xml_declaration=True)
    ET.parse(target_path)
    print(f"BOAT v4 EPG merged: channels={len(source_channels)} programmes={len(source_programmes)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["streams", "epg", "all"])
    args = ap.parse_args()
    if args.phase in ("streams", "all"):
        sync_streams()
    if args.phase in ("epg", "all"):
        merge_epg()


if __name__ == "__main__":
    main()
