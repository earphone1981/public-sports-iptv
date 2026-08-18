from pathlib import Path
import subprocess

COOKIES = 'youtube_cookies.txt'
M3U = Path('public_sports.m3u')

# ============================================================
# 一発更新用 YouTube BASE
# ・公営競技のYouTubeサブは完全廃止
# ・「かなチューブ」は youtube_dynamic_update.py 側
# ・ここでは「その他LIVE」だけ更新する
# ============================================================

SOURCES = [
    # 固定動画IDで安定しているもの
    ('ナミビア', 'https://www.youtube.com/watch?v=ydYDqZQpim8',
     'youtube.namibia.live', '🇳🇦 ナミビア LIVE', 'namibia_live.m3u'),
    ('松山市クリーンセンター', 'https://www.youtube.com/watch?v=C0gpM_qIIl0',
     'youtube.matsuyama.clean', '♻️ 松山市クリーンセンター LIVE', 'youtube_test.m3u'),
    ('松山空港', 'https://www.youtube.com/watch?v=CFh9z-6IeEE',
     'youtube.matsuyama.airport', '✈️ 松山空港 LIVE', 'matsuyama_airport_live.m3u'),
    ('大阪環状線', 'https://www.youtube.com/watch?v=HYQHcAqNBms',
     'youtube.osaka.loop.live', '🚃 大阪環状線 LIVE', ''),

    # 配信動画IDが変わっても一発更新で現行LIVEを探すもの
    ('道後温泉本館', 'ytsearch3:道後温泉本館 ライブカメラ LIVE',
     'youtube.dogo.live', '♨️ 道後温泉本館 LIVE', ''),
    ('松山市本町', 'ytsearch3:松山市本町 ライブカメラ 南海放送NEWS LIVE',
     'youtube.matsuyama.honmachi.live', '🏙️ 松山市本町 LIVE', ''),
    ('八幡浜港', 'ytsearch3:八幡浜港 フェリーターミナル ライブカメラ LIVE',
     'youtube.yawatahama.port.live', '⛴️ 八幡浜港 LIVE', ''),
    ('宇和島', 'ytsearch5:宇和島 ライブカメラ テレビ愛媛 LIVE',
     'youtube.uwajima.live', '🏯 宇和島 LIVE', ''),
    ('しまなみ', 'ytsearch5:しまなみ ライブカメラ テレビ愛媛 LIVE',
     'youtube.shimanami.live', '🌉 しまなみ LIVE', ''),
]


def get_url(source):
    cmd = [
        'yt-dlp',
        '--js-runtimes', 'node',
        '--cookies', COOKIES,
        '--extractor-args', 'youtube:player_client=default,web_safari',
        '--no-playlist',
        '--match-filter', 'is_live',
        '--no-warnings',
        '-f', '95/best[protocol^=m3u8]/best',
        '-g', source,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    urls = [
        x.strip() for x in p.stdout.splitlines()
        if x.strip().startswith(('http://', 'https://'))
    ]
    return urls[0] if p.returncode == 0 and urls else None


def ext(label, tvg, display):
    return (
        f'#EXTINF:-1 tvg-id="{tvg}" tvg-name="{label} LIVE" '
        f'group-title="その他LIVE",{display}'
    )


results = []
for label, source, tvg, display, file_name in SOURCES:
    try:
        url = get_url(source)
    except Exception as e:
        print('ERR', label, e)
        url = None

    if not url:
        print('NO LIVE', label)
        continue

    print('OK', label)
    results.append((label, tvg, display, url))

    if file_name:
        Path(file_name).write_text(
            '#EXTM3U\n' + ext(label, tvg, display) + '\n' + url + '\n',
            encoding='utf-8',
        )

text = M3U.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
start = '# === BASE YOUTUBE LIVE START ==='
end = '# === BASE YOUTUBE LIVE END ==='

# 旧BASE形式・旧公営サブを除去
lines = text.split('\n')
out = []
i = 0
while i < len(lines):
    line = lines[i]

    if line.strip() == '# === BASE YOUTUBE LIVE ===':
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('# === DYNAMIC YOUTUBE LIVE START ==='):
            i += 1
        continue

    if line.strip() == start:
        i += 1
        while i < len(lines) and lines[i].strip() != end:
            i += 1
        if i < len(lines):
            i += 1
        continue

    # 公営競技YouTubeサブは残さない
    if line.startswith('#EXTINF:') and any(g in line for g in [
        '競輪 YouTube LIVE',
        '地方競馬 YouTube LIVE',
        'オートレース YouTube LIVE',
        'ボートレース YouTube LIVE',
        '公営競技 横断LIVE',
    ]):
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith('#EXTINF:') or s.startswith('## ') or s.startswith('# ==='):
                break
            i += 1
        continue

    if line.strip() in {
        '## 競輪 YouTube LIVE',
        '## 地方競馬 YouTube LIVE',
        '## オートレース YouTube LIVE',
        '## ボートレース YouTube LIVE',
        '## 公営競技 横断LIVE',
    }:
        i += 1
        continue

    out.append(line.rstrip())
    i += 1

while out and not out[-1].strip():
    out.pop()

out += ['', start]
for label, tvg, display, url in results:
    out += ['## その他LIVE', ext(label, tvg, display), url, '']
out += [end, '']

M3U.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')
print('BASE その他LIVE COUNT', len(results))
