from pathlib import Path
import json
import subprocess
import sys

BASE = Path(__file__).resolve().parent

FIXED_LIVES = [
    {
        "label": "松山市クリーンセンター",
        "url": "https://www.youtube.com/watch?v=C0gpM_qIIl0",
        "out": BASE / "youtube_test.m3u",
        "tvg_id": "youtube.matsuyama.clean",
        "display": "♻️ 松山市クリーンセンター LIVE",
        "group": "その他LIVE",
    },
    {
        "label": "ナミビアLIVE",
        "url": "https://www.youtube.com/watch?v=ydYDqZQpim8",
        "out": BASE / "namibia_live.m3u",
        "tvg_id": "youtube.namibia.live",
        "display": "🇳🇦 ナミビア LIVE",
        "group": "その他LIVE",
    },
    {
        "label": "松山空港LIVE",
        "url": "https://www.youtube.com/watch?v=CFh9z-6IeEE",
        "out": BASE / "matsuyama_airport_live.m3u",
        "tvg_id": "youtube.matsuyama.airport",
        "display": "✈️ 松山空港 LIVE",
        "group": "その他LIVE",
    },
]

EHIME_MP = {
    "url": "https://www.youtube.com/@EhimeMandarinPirates/live",
    "out": BASE / "ehime_mp_home_live.m3u",
    "tvg_id": "youtube.ehime.mp.home",
    "display": "⚾ 愛媛マンダリンパイレーツ HOME LIVE",
    "group": "野球LIVE",
}

BOAT_CHANNELS = {
    "桐生": "UCT2pRt_me0tOA8B2sakEv7Q",
    "戸田": "UCoLCf3aVRMSukwetHfn1p1A",
    "江戸川": "UCpNAwETM_vPV2Skumzc_KMA",
    "平和島": "UCGExstl4XKMun5eY9V0zlSg",
    "多摩川": "UC4lvZQUptR8m5VDSu49xCGQ",
    "浜名湖": "UCGZig6i5JrZ33jjW2GG6Bzw",
    "蒲郡": "UCZhuyNQgLORLjgl8hlA7uHw",
    "常滑": "UCu9lPbAk1MosTGm2yQ4BapQ",
    "津": "UCEUXzh5FRxDneaLvv0YdEfQ",
    "三国": "UCu-yP6WJQ0zcx5nmWhxvJEg",
    "びわこ": "UCLbcsJqsT5Qa1axpYcOBpmg",
    "住之江": "UCW3AReETO-oDmEoE-m3i7dQ",
    "尼崎": "UC-vpH4QQKPwsqsbESOfNgZQ",
    "鳴門": "UCd8rJfg7p8qsASOEIIwAinQ",
    "丸亀": "UC2CWDMG18mpBGXkI9KHdACQ",
    "児島": "UC6IrOXVuw6xXLl1qJqYUrsg",
    "宮島": "UCxvYC6PPCsy2_p0tGuvIv5w",
    "徳山": "UCqyq1Dav7D5ztEl_ierxsjw",
    "下関": "UCl-7IwVjJHzWUhqxz7hwY1w",
    "若松": "UCll--OtE3eJpzb4uwX8MX9A",
    "芦屋": "UC5BunThJ_eBJq5gz-DOaRLw",
    "福岡": "UCgyb8el3rLkg8i0bEMboQhA",
    "唐津": "UCO6ycDxAk-5OHAiKc71gNSQ",
    "大村": "UCPLb9R1EIqxNBy8Qzcrz8Wg",
}

BOAT_TVG_ID = {
    "桐生": "boat.kiryu",
    "戸田": "boat.toda",
    "江戸川": "boat.edogawa",
    "平和島": "boat.heiwajima",
    "多摩川": "boat.tamagawa",
    "浜名湖": "boat.hamanako",
    "蒲郡": "boat.gamagori",
    "常滑": "boat.tokoname",
    "津": "boat.tsu",
    "三国": "boat.mikuni",
    "びわこ": "boat.biwako",
    "住之江": "boat.suminoe",
    "尼崎": "boat.amagasaki",
    "鳴門": "boat.naruto",
    "丸亀": "boat.marugame",
    "児島": "boat.kojima",
    "宮島": "boat.miyajima",
    "徳山": "boat.tokuyama",
    "下関": "boat.shimonoseki",
    "若松": "boat.wakamatsu",
    "芦屋": "boat.ashiya",
    "福岡": "boat.fukuoka",
    "唐津": "boat.karatsu",
    "大村": "boat.omura",
}

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

def get_live_url(url):
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-playlist",
        "--match-filter", "is_live",
        "--no-warnings",
        "-f", "best[acodec!=none][vcodec!=none]/best",
        "-g", url,
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception:
        return None

    if p.returncode != 0:
        return None

    urls = [
        x.strip() for x in p.stdout.splitlines()
        if x.strip().startswith(("http://", "https://"))
    ]
    return urls[0] if urls else None

def write_one(path, tvg_id, display, group, url):
    if not url:
        path.write_text("#EXTM3U\n", encoding="utf-8")
        return

    path.write_text(
        "#EXTM3U\n"
        f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="{group}",{display}\n'
        f"{url}\n",
        encoding="utf-8",
    )

def main():
    if not ensure_ytdlp():
        return 0

    for item in FIXED_LIVES:
        url = get_live_url(item["url"])
        write_one(
            item["out"],
            item["tvg_id"],
            item["display"],
            item["group"],
            url,
        )

    url = get_live_url(EHIME_MP["url"])
    write_one(
        EHIME_MP["out"],
        EHIME_MP["tvg_id"],
        EHIME_MP["display"],
        EHIME_MP["group"],
        url,
    )

    lines = ["#EXTM3U", ""]

    for name, channel_id in BOAT_CHANNELS.items():
        url = get_live_url(
            f"https://www.youtube.com/channel/{channel_id}/live"
        )

        if not url:
            continue

        tvg_id = BOAT_TVG_ID[name]

        lines += [
            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name} YouTube LIVE" group-title="ボートレース YouTube LIVE",📺 {name} 公式YouTube LIVE',
            url,
            "",
        ]

    (BASE / "boatrace_youtube_backup.m3u").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
