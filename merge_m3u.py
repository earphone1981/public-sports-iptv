from pathlib import Path
from urllib.parse import quote

# ============================================================
# 公営まとめ M3U - 一発更新用
#
# ・競輪・地方競馬・オート・ボートを統合
# ・YouTube系は「かなチューブ」と「その他LIVE」だけ残す
# ・各公営競技のYouTubeサブチャンネルは統合しない
# ・中央競馬は GitHub 上の HQ 4本 + LQ 4本 = 8ch
# ・EPGは GitHub上の epg.xml を読み込む
# ============================================================

INPUTS = [
    ("競輪", Path("keirin_master.m3u")),
    ("地方競馬", Path("keiba_master.m3u")),
    ("オートレース", Path("autorace_master.m3u")),
    ("ボートレース", Path("boatrace_today.m3u")),
]

YOUTUBE_INPUTS = [
    ("かなチューブ", Path("kana_live.m3u")),
    ("その他LIVE", Path("youtube_test.m3u")),
    ("その他LIVE", Path("namibia_live.m3u")),
    ("その他LIVE", Path("matsuyama_airport_live.m3u")),
]

OUT = Path("public_sports.m3u")

GITHUB_USER = "earphone1981"
GITHUB_REPO = "public-sports-iptv"
GITHUB_BRANCH = "main"

EPG_URL = (
    "https://raw.githubusercontent.com/"
    f"{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/epg.xml"
)

JRA_CHANNELS = [
    {"tvg_id":"jra.gch","tvg_name":"グリーンチャンネル","display_name":"グリーンチャンネル（高画質）","file":"gchmain.m3u8"},
    {"tvg_id":"jra.gch","tvg_name":"グリーンチャンネル","display_name":"グリーンチャンネル（低画質）","file":"gchmain_LQ.m3u8"},
    {"tvg_id":"jra.east","tvg_name":"JRA EAST","display_name":"JRA EAST（高画質）","file":"EAST_test.m3u8"},
    {"tvg_id":"jra.east","tvg_name":"JRA EAST","display_name":"JRA EAST（低画質）","file":"EAST_test_LQ.m3u8"},
    {"tvg_id":"jra.west","tvg_name":"JRA WEST","display_name":"JRA WEST（高画質）","file":"WEST_master .m3u8"},
    {"tvg_id":"jra.west","tvg_name":"JRA WEST","display_name":"JRA WEST（低画質）","file":"WEST_master_LQ.m3u8"},
    {"tvg_id":"jra.hokkaido","tvg_name":"JRA HOKKAIDO","display_name":"JRA HOKKAIDO（高画質）","file":"hokaido_master (1).m3u8"},
    {"tvg_id":"jra.hokkaido","tvg_name":"JRA HOKKAIDO","display_name":"JRA HOKKAIDO（低画質）","file":"hokaido_master_LQ.m3u8"},
]


def read_entries(path: Path):
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]

    entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            options = []
            url = ""
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt:
                    j += 1
                    continue
                if nxt.startswith("#EXTINF:"):
                    break
                if nxt.startswith("#EXTVLCOPT:"):
                    options.append(nxt)
                    j += 1
                    continue
                if not nxt.startswith("#"):
                    url = nxt
                    break
                j += 1
            if url:
                entries.append((extinf, options, url))
        i += 1
    return entries


def raw_github_url(filename: str) -> str:
    encoded = quote(filename)
    return (
        f"https://raw.githubusercontent.com/"
        f"{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{encoded}"
    )


def append_entries(out, entries):
    for extinf, options, url in entries:
        out.append(extinf)
        out.extend(options)
        out.append(url)
        out.append("")


def main():
    out = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]
    total = 0

    # 公営4競技
    for label, path in INPUTS:
        entries = read_entries(path)
        if not entries:
            print(f"{label}: 0 ch <- {path.name}")
            continue
        print(f"{label}: {len(entries)} ch <- {path.name}")
        out.append(f"## {label}")
        append_entries(out, entries)
        total += len(entries)

    # YouTube系：かなチューブ + その他LIVEのみ
    for label, path in YOUTUBE_INPUTS:
        entries = read_entries(path)
        if not entries:
            print(f"{label}: 現在LIVEなし <- {path.name}")
            continue
        print(f"{label}: {len(entries)} ch <- {path.name}")
        out.append(f"## {label}")
        append_entries(out, entries)
        total += len(entries)

    # 中央競馬 HQ/LQ
    out.append("## 中央競馬")
    for ch in JRA_CHANNELS:
        raw_url = raw_github_url(ch["file"])
        extinf = (
            f'#EXTINF:-1 '
            f'tvg-id="{ch["tvg_id"]}" '
            f'tvg-name="{ch["tvg_name"]}" '
            f'group-title="中央競馬",'
            f'{ch["display_name"]}'
        )
        out.extend([extinf, raw_url, ""])
        total += 1

    OUT.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    print("============================")
    print("M3U一本化 完了")
    print(f"合計チャンネル数: {total}")
    print("YouTube: かなチューブ + その他LIVEのみ")
    print(f"EPG: {EPG_URL}")
    print(f"出力: {OUT}")
    print("============================")


if __name__ == "__main__":
    main()
