from pathlib import Path

INPUTS = [
    ("競輪", Path("keirin_master.m3u")),
    ("地方競馬", Path("keiba_master.m3u")),
    ("オートレース", Path("autorace_master.m3u")),
    ("ボートレース", Path("boatrace_today.m3u")),
]

OUT = Path("public_sports.m3u")


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


def main():
    out = ["#EXTM3U", ""]
    total = 0

    for label, path in INPUTS:
        entries = read_entries(path)
        print(f"{label}: {len(entries)} ch <- {path.name}")
        out.append(f"## {label}")

        for extinf, url in entries:
            out.append(extinf)
            out.append(url)
            out.append("")

        total += len(entries)

    OUT.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    print("")
    print("============================")
    print("M3U一本化 完了")
    print(f"合計チャンネル数: {total}")
    print(f"出力: {OUT}")
    print("============================")


if __name__ == "__main__":
    main()
