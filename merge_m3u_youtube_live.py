from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).resolve().parent

EPG_URL = "https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main/epg.xml"

INPUTS = [
    ("競輪", BASE / "keirin_master.m3u"),
    ("地方競馬", BASE / "keiba_master.m3u"),
    ("オートレース", BASE / "autorace_master.m3u"),
    ("ボートレース", BASE / "boatrace_today.m3u"),
]

YOUTUBE_INPUTS = [
    ("競輪 YouTube LIVE", BASE / "kana_live.m3u"),
    ("その他LIVE", BASE / "youtube_test.m3u"),
    ("その他LIVE", BASE / "namibia_live.m3u"),
    ("その他LIVE", BASE / "matsuyama_airport_live.m3u"),
    ("野球LIVE", BASE / "ehime_mp_home_live.m3u"),
    ("ボートレース YouTube LIVE", BASE / "boatrace_youtube_backup.m3u"),
]

JRA = [
    ("jra.gch","グリーンチャンネル","グリーンチャンネル（高画質）","gchmain.m3u8"),
    ("jra.gch","グリーンチャンネル","グリーンチャンネル（低画質）","gchmain_LQ.m3u8"),
    ("jra.east","JRA EAST","JRA EAST（高画質）","EAST_test.m3u8"),
    ("jra.east","JRA EAST","JRA EAST（低画質）","EAST_test_LQ.m3u8"),
    ("jra.west","JRA WEST","JRA WEST（高画質）","WEST_master .m3u8"),
    ("jra.west","JRA WEST","JRA WEST（低画質）","WEST_master_LQ.m3u8"),
    ("jra.hokkaido","JRA HOKKAIDO","JRA HOKKAIDO（高画質）","hokaido_master (1).m3u8"),
    ("jra.hokkaido","JRA HOKKAIDO","JRA HOKKAIDO（低画質）","hokaido_master_LQ.m3u8"),
]

def read_entries(path):
    if not path.exists():
        return []

    lines = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    ).splitlines()

    entries = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            j = i + 1

            while j < len(lines):
                nxt = lines[j].strip()

                if not nxt:
                    j += 1
                    continue

                if nxt.startswith("#EXTINF:"):
                    break

                if not nxt.startswith("#"):
                    entries.append((line, nxt))
                    break

                j += 1

        i += 1

    return entries

def raw(filename):
    return (
        "https://raw.githubusercontent.com/"
        "earphone1981/public-sports-iptv/main/"
        + quote(filename)
    )

def main():
    out = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]

    for label, path in INPUTS:
        entries = read_entries(path)

        if not entries:
            continue

        out.append(f"## {label}")

        for extinf, url in entries:
            out += [extinf, url, ""]

    for label, path in YOUTUBE_INPUTS:
        entries = read_entries(path)

        if not entries:
            continue

        out.append(f"## {label}")

        for extinf, url in entries:
            out += [extinf, url, ""]

    out.append("## 中央競馬")

    for tvg_id, tvg_name, display, filename in JRA:
        out += [
            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}" group-title="中央競馬",{display}',
            raw(filename),
            "",
        ]

    (BASE / "public_sports.m3u").write_text(
        "\n".join(out).rstrip() + "\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
