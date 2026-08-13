from pathlib import Path
from urllib.parse import quote

# ============================================================
# 公営まとめ M3U
# 競輪・地方競馬・オートは master を全場常設
# ボートは当日取得分だけ
# 中央競馬/GCH 4ch は GitHub上の m3u8 をそのまま子プレイリストとして参照
# ============================================================

INPUTS = [
    ("競輪", Path("keirin_master.m3u")),
    ("地方競馬", Path("keiba_master.m3u")),
    ("オートレース", Path("autorace_master.m3u")),
    ("ボートレース", Path("boatrace_today.m3u")),
]

OUT = Path("public_sports.m3u")

GITHUB_USER = "earphone1981"
GITHUB_REPO = "public-sports-iptv"
GITHUB_BRANCH = "main"

JRA_CHANNELS = [
    {
        "tvg_id": "jra.gch",
        "tvg_name": "グリーンチャンネル",
        "display_name": "グリーンチャンネル",
        "file": "gchmain.m3u8",
    },
    {
        "tvg_id": "jra.east",
        "tvg_name": "JRA EAST",
        "display_name": "JRA EAST",
        "file": "EAST_test.m3u8",
    },
    {
        "tvg_id": "jra.west",
        "tvg_name": "JRA WEST",
        "display_name": "JRA WEST",
        "file": "WEST_master .m3u8",
    },
    {
        "tvg_id": "jra.hokkaido",
        "tvg_name": "JRA HOKKAIDO",
        "display_name": "JRA HOKKAIDO",
        "file": "hokaido_master (1).m3u8",
    },
]


def read_entries(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} がありません")

    text = path.read_text(encoding="utf-8-sig")
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]

    entries = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            extinf = line
            url = ""

            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()

                if not nxt:
                    j += 1
                    continue

                if nxt.startswith("#EXTINF:"):
                    break

                if not nxt.startswith("#"):
                    url = nxt
                    break

                j += 1

            if url:
                entries.append((extinf, url))

        i += 1

    return entries


def raw_github_url(filename: str) -> str:
    # ファイル名の空白・括弧などをURLエンコード
    encoded = quote(filename)
    return (
        f"https://raw.githubusercontent.com/"
        f"{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{encoded}"
    )


def main():
    out = ["#EXTM3U", ""]
    total = 0

    # --------------------------------------------------------
    # 既存4競技
    # --------------------------------------------------------
    for label, path in INPUTS:
        entries = read_entries(path)
        print(f"{label}: {len(entries)} ch <- {path.name}")

        out.append(f"## {label}")

        for extinf, url in entries:
            out.append(extinf)
            out.append(url)
            out.append("")

        total += len(entries)

    # --------------------------------------------------------
    # 中央競馬 / GCH 4ch
    # --------------------------------------------------------
    out.append("## 中央競馬")

    for ch in JRA_CHANNELS:
        source_file = Path(ch["file"])

        if not source_file.exists():
            raise FileNotFoundError(
                f"中央競馬ファイルがありません: {source_file}"
            )

        raw_url = raw_github_url(ch["file"])

        extinf = (
            f'#EXTINF:-1 '
            f'tvg-id="{ch["tvg_id"]}" '
            f'tvg-name="{ch["tvg_name"]}" '
            f'group-title="中央競馬",'
            f'{ch["display_name"]}'
        )

        out.append(extinf)
        out.append(raw_url)
        out.append("")

        print(
            f'中央競馬: {ch["display_name"]} '
            f'<- {ch["file"]}'
        )

        total += 1

    OUT.write_text(
        "\n".join(out).rstrip() + "\n",
        encoding="utf-8",
    )

    print("")
    print("============================")
    print("M3U一本化 完了")
    print(f"合計チャンネル数: {total}")
    print("中央競馬追加: 4 ch")
    print(f"出力: {OUT}")
    print("============================")


if __name__ == "__main__":
    main()
