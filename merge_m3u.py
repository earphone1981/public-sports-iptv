from pathlib import Path
from urllib.parse import quote
import re

# ============================================================
# 公営まとめ M3U - 一発更新用
# ・競輪・地方競馬・オート・ボートを統合
# ・YouTube系は「かなチューブ」と「その他LIVE」だけ残す
# ・中央競馬は GitHub 上の HQ 4本 + LQ 4本 = 8ch
# ・EPGは GitHub上の epg.xml
# ・競輪 / YouTube / LIVE系は tvg-id でGitHub新ロゴを自動付与
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
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
EPG_URL = f"{RAW_BASE}/epg.xml"

KEIRIN_LOGO_DIR = "public_sports_logos_github_43/keirin_logos_github_ready"

LOGO_BY_TVG_ID = {
    # 競輪 43ch（確定マスター）
    "keirin.hakodate": f"{KEIRIN_LOGO_DIR}/hakodate.png",
    "keirin.aomori": f"{KEIRIN_LOGO_DIR}/aomori.png",
    "keirin.iwakitaira": f"{KEIRIN_LOGO_DIR}/iwakitaira.png",
    "keirin.yahiko": f"{KEIRIN_LOGO_DIR}/yahiko.png",
    "keirin.maebashi": f"{KEIRIN_LOGO_DIR}/maebashi.png",
    "keirin.toride": f"{KEIRIN_LOGO_DIR}/toride.png",
    "keirin.utsunomiya": f"{KEIRIN_LOGO_DIR}/utsunomiya.png",
    "keirin.omiya": f"{KEIRIN_LOGO_DIR}/omiya.png",
    "keirin.seibuen": f"{KEIRIN_LOGO_DIR}/seibuen.png",
    "keirin.keiogatsu": f"{KEIRIN_LOGO_DIR}/keiokaku.png",
    "keirin.tachikawa": f"{KEIRIN_LOGO_DIR}/tachikawa.png",
    "keirin.matsudo": f"{KEIRIN_LOGO_DIR}/matsudo.png",
    "keirin.kawasaki": f"{KEIRIN_LOGO_DIR}/kawasaki.png",
    "keirin.hiratsuka": f"{KEIRIN_LOGO_DIR}/hiratsuka.png",
    "keirin.odawara": f"{KEIRIN_LOGO_DIR}/odawara.png",
    "keirin.ito": f"{KEIRIN_LOGO_DIR}/ito.png",
    "keirin.shizuoka": f"{KEIRIN_LOGO_DIR}/shizuoka.png",
    "keirin.nagoya": f"{KEIRIN_LOGO_DIR}/nagoya.png",
    "keirin.gifu": f"{KEIRIN_LOGO_DIR}/gifu.png",
    "keirin.ogaki": f"{KEIRIN_LOGO_DIR}/ogaki.png",
    "keirin.toyohashi": f"{KEIRIN_LOGO_DIR}/toyohashi.png",
    "keirin.toyama": f"{KEIRIN_LOGO_DIR}/toyama.png",
    "keirin.matsusaka": f"{KEIRIN_LOGO_DIR}/matsusaka.png",
    "keirin.yokkaichi": f"{KEIRIN_LOGO_DIR}/yokkaichi.png",
    "keirin.fukui": f"{KEIRIN_LOGO_DIR}/fukui.png",
    "keirin.nara": f"{KEIRIN_LOGO_DIR}/nara.png",
    "keirin.mukomachi": f"{KEIRIN_LOGO_DIR}/mukomachi.png",
    "keirin.wakayama": f"{KEIRIN_LOGO_DIR}/wakayama.png",
    "keirin.kishiwada": f"{KEIRIN_LOGO_DIR}/kishiwada.png",
    "keirin.tamano": f"{KEIRIN_LOGO_DIR}/tamano.png",
    "keirin.hiroshima": f"{KEIRIN_LOGO_DIR}/hiroshima.png",
    "keirin.hofu": f"{KEIRIN_LOGO_DIR}/hofu.png",
    "keirin.takamatsu": f"{KEIRIN_LOGO_DIR}/takamatsu.png",
    "keirin.komatsushima": f"{KEIRIN_LOGO_DIR}/komatsushima.png",
    "keirin.kochi": f"{KEIRIN_LOGO_DIR}/kochi.png",
    "keirin.matsuyama": f"{KEIRIN_LOGO_DIR}/matsuyama.png",
    "keirin.kokura": f"{KEIRIN_LOGO_DIR}/kokura.png",
    "keirin.kurume": f"{KEIRIN_LOGO_DIR}/kurume.png",
    "keirin.takeo": f"{KEIRIN_LOGO_DIR}/takeo.png",
    "keirin.sasebo": f"{KEIRIN_LOGO_DIR}/sasebo.png",
    "keirin.beppu": f"{KEIRIN_LOGO_DIR}/beppu.png",
    "keirin.kumamoto": f"{KEIRIN_LOGO_DIR}/kumamoto.png",
    "keirin.pist6": f"{KEIRIN_LOGO_DIR}/pist6.png",

    # 現行 その他LIVE / かなチューブ
    "youtube.kana.live": "public_sports_logos_github_43/youtube_live/kana_tube.png",
    "youtube.namibia.live": "public_sports_logos_github_43/youtube_live/namibia_live.png",
    "youtube.matsuyama.clean": "public_sports_logos_github_43/youtube_live/matsuyama_clean.png",
    "youtube.matsuyama.airport": "public_sports_logos_github_43/youtube_live/matsuyama_airport.png",
    "youtube.dogo.live": "public_sports_logos_github_43/youtube_live/dogo_live.png",
    "youtube.matsuyama.honmachi.live": "public_sports_logos_github_43/youtube_live/matsuyama_honmachi.png",
    "youtube.yawatahama.port.live": "public_sports_logos_github_43/youtube_live/yawatahama_port.png",
    "youtube.uwajima.live": "public_sports_logos_github_43/youtube_live/uwajima_live.png",
    "youtube.shimanami.live": "public_sports_logos_github_43/youtube_live/shimanami_live.png",
}

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
    return f"{RAW_BASE}/{encoded}"


def apply_logo(extinf: str) -> str:
    m = re.search(r'tvg-id="([^"]+)"', extinf)
    if not m:
        return extinf
    tvg_id = m.group(1)
    rel = LOGO_BY_TVG_ID.get(tvg_id)
    if not rel:
        return extinf
    logo = f"{RAW_BASE}/{rel}"
    if 'tvg-logo="' in extinf:
        return re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo}"', extinf, count=1)
    pos = extinf.find('group-title="')
    if pos >= 0:
        return extinf[:pos] + f'tvg-logo="{logo}" ' + extinf[pos:]
    comma = extinf.find(',')
    if comma >= 0:
        return extinf[:comma] + f' tvg-logo="{logo}"' + extinf[comma:]
    return extinf


def append_entries(out, entries):
    for extinf, options, url in entries:
        out.append(apply_logo(extinf))
        out.extend(options)
        out.append(url)
        out.append("")


def main():
    out = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]
    total = 0
    for label, path in INPUTS:
        entries = read_entries(path)
        if not entries:
            print(f"{label}: 0 ch <- {path.name}")
            continue
        print(f"{label}: {len(entries)} ch <- {path.name}")
        out.append(f"## {label}")
        append_entries(out, entries)
        total += len(entries)
    for label, path in YOUTUBE_INPUTS:
        entries = read_entries(path)
        if not entries:
            print(f"{label}: 現在LIVEなし <- {path.name}")
            continue
        print(f"{label}: {len(entries)} ch <- {path.name}")
        out.append(f"## {label}")
        append_entries(out, entries)
        total += len(entries)
    out.append("## 中央競馬")
    for ch in JRA_CHANNELS:
        raw_url = raw_github_url(ch["file"])
        extinf = (
            f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" '
            f'tvg-name="{ch["tvg_name"]}" '
            f'group-title="中央競馬",{ch["display_name"]}'
        )
        out.extend([extinf, raw_url, ""])
        total += 1
    OUT.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print("============================")
    print("M3U一本化 完了")
    print(f"合計チャンネル数: {total}")
    print("競輪 / YouTube / LIVEロゴ: GitHub新ロゴを自動付与")
    print(f"EPG: {EPG_URL}")
    print(f"出力: {OUT}")
    print("============================")


if __name__ == "__main__":
    main()
