from pathlib import Path
import json
import subprocess

COOKIES = 'youtube_cookies.txt'
M3U = Path('public_sports.m3u')

# ============================================================
# 一発更新用 YouTube DYNAMIC
# ・公営競技のYouTubeサブは完全廃止
# ・ここでは「かなチューブ」だけを拾う
# ・LIVEなし時も「現在LIVEなし」をM3Uに常設する
# ・同じ tvg-id は更新前に必ず除去して重複させない
# ============================================================

KANA_STREAMS = 'https://www.youtube.com/@kana_tube/streams'
KANA_CHANNEL = 'https://www.youtube.com/@kana_tube/streams'
KANA_TVG_ID = 'youtube.kana.live'


def run(cmd, timeout=180):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def live_items(src):
    p = run([
        'yt-dlp',
        '--cookies', COOKIES,
        '--flat-playlist',
        '--dump-json',
        '--playlist-end', '20',
        src,
    ])

    out = []
    for line in p.stdout.splitlines():
        try:
            item = json.loads(line)
        except Exception:
            continue

        if item.get('live_status') == 'is_live' or item.get('is_live'):
            vid = item.get('id')
            if vid:
                out.append((
                    item.get('title') or '華奈tube LIVE',
                    f'https://www.youtube.com/watch?v={vid}',
                ))
    return out


def get_url(page):
    p = run([
        'yt-dlp',
        '--js-runtimes', 'node',
        '--cookies', COOKIES,
        '--extractor-args', 'youtube:player_client=default,web_safari',
        '--no-playlist',
        '--match-filter', 'is_live',
        '--no-warnings',
        '-f', '95/best[protocol^=m3u8]/best',
        '-g', page,
    ], 150)

    urls = [
        x.strip() for x in p.stdout.splitlines()
        if x.strip().startswith(('http://', 'https://'))
    ]
    return urls[0] if p.returncode == 0 and urls else None


def skip_entry(lines, i):
    i += 1
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith('#EXTINF:') or s.startswith('## ') or s.startswith('# ==='):
            break
        i += 1
    return i


entries = []
try:
    items = live_items(KANA_STREAMS)
except Exception as e:
    print('KANA LIST ERROR', e)
    items = []

for title, page in items:
    try:
        url = get_url(page)
    except Exception as e:
        print('KANA URL ERROR', title, e)
        url = None

    if url:
        name = f'📺 華奈tube｜{title}'
        ext = (
            f'#EXTINF:-1 tvg-id="{KANA_TVG_ID}" '
            'tvg-name="華奈tube LIVE" group-title="かなチューブ",'
            + name
        )
        entries.append((ext, url))
        print('OK KANA', title)
        break

if entries:
    display_ext, display_url = entries[0]
else:
    display_ext = (
        f'#EXTINF:-1 tvg-id="{KANA_TVG_ID}" '
        'tvg-name="華奈tube LIVE" group-title="かなチューブ",'
        '📺 華奈tube｜現在LIVEなし'
    )
    display_url = KANA_CHANNEL
    print('KANA OFFLINE PLACEHOLDER')

Path('kana_live.m3u').write_text(
    '#EXTM3U\n' + display_ext + '\n' + display_url + '\n',
    encoding='utf-8'
)

text = M3U.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
start = '# === DYNAMIC YOUTUBE LIVE START ==='
end = '# === DYNAMIC YOUTUBE LIVE END ==='

if start in text and end in text:
    before = text.split(start, 1)[0].rstrip()
    after = text.split(end, 1)[1].lstrip()
    text = before + '\n' + after

lines = text.split('\n')
out = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # マーカー外に残った旧かなチューブも必ず削除する。
    if line.startswith('#EXTINF:') and f'tvg-id="{KANA_TVG_ID}"' in line:
        i = skip_entry(lines, i)
        continue

    if line.startswith('#EXTINF:') and any(g in line for g in [
        '競輪 YouTube LIVE',
        '地方競馬 YouTube LIVE',
        'オートレース YouTube LIVE',
        'ボートレース YouTube LIVE',
        '公営競技 横断LIVE',
    ]):
        i = skip_entry(lines, i)
        continue

    if stripped in {
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

block = [
    '',
    start,
    '## かなチューブ',
    display_ext,
    display_url,
    '',
    end,
    ''
]

M3U.write_text(
    '\n'.join(out).rstrip() + '\n' + '\n'.join(block),
    encoding='utf-8'
)
print('DYNAMIC KANA LIVE COUNT', len(entries))
