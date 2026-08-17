from pathlib import Path
import subprocess
import sys

CHANNEL_URL = "https://www.youtube.com/@kana_tube/live"
OUT = Path(__file__).with_name("kana_live.m3u")
LOGO_URL = "https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main/kana_tube.png"

def ensure_ytdlp():
    try:
        import yt_dlp
        return True
    except Exception:
        p = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
            text=True,
        )
        return p.returncode == 0

def write_empty(reason):
    OUT.write_text("#EXTM3U\n# 華奈tube: " + reason + "\n", encoding="utf-8")

def main():
    if not ensure_ytdlp():
        write_empty("yt-dlp利用不可")
        return 0

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-playlist",
        "--match-filter", "is_live",
        "--no-warnings",
        "-f", "best[acodec!=none][vcodec!=none]/best",
        "-g",
        CHANNEL_URL,
    ]

    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except Exception as e:
        write_empty(str(e))
        return 0

    urls = [
        x.strip() for x in p.stdout.splitlines()
        if x.strip().startswith(("http://", "https://"))
    ]

    if p.returncode != 0 or not urls:
        write_empty("現在LIVEなし / 取得できず")
        return 0

    OUT.write_text(
        "#EXTM3U\n"
        f'#EXTINF:-1 tvg-id="youtube.kana" tvg-name="華奈tube LIVE" tvg-logo="{LOGO_URL}" group-title="競輪 YouTube LIVE",📺 華奈tube LIVE\n'
        + urls[0] + "\n",
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
