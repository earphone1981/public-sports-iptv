from pathlib import Path
import re
from urllib.parse import urlsplit

PATH = Path('public_sports_youtube.m3u')


def attr(ext, name):
    m = re.search(rf'{re.escape(name)}="([^"]*)"', ext)
    return m.group(1).strip() if m else ''


def canonical_url(url):
    """Ignore short-lived query tokens when comparing the same live stream."""
    try:
        p = urlsplit(url.strip())
        return f'{p.scheme}://{p.netloc}{p.path}'
    except Exception:
        return url.split('?', 1)[0].strip()


def read_entries(text):
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith('#EXTINF:'):
            i += 1
            continue
        block = [line]
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith('#EXTINF:') or s.startswith('## '):
                break
            if s:
                block.append(s)
            i += 1
            if s and not s.startswith('#'):
                break
        url = next((x for x in reversed(block) if x.startswith(('http://','https://'))), '')
        if url:
            entries.append((block, url))
    return entries


if not PATH.exists():
    raise SystemExit('public_sports_youtube.m3u not found')

text = PATH.read_text(encoding='utf-8-sig', errors='replace')
entries = read_entries(text)

seen_tvg = set()
seen_stream = set()
out = ['#EXTM3U', '']
last_group = None
kept = 0
removed = 0

for block, url in entries:
    ext = block[0]
    tvg = attr(ext, 'tvg-id')
    group = attr(ext, 'group-title') or '公営YouTube'
    stream_key = canonical_url(url)

    # Same tvg-id must never appear twice.
    if tvg and tvg in seen_tvg:
        removed += 1
        continue

    # Same resolved live stream must never be registered under multiple venue rows.
    # This catches shared official channels such as 園田/姫路 and 盛岡/水沢.
    if stream_key and stream_key in seen_stream:
        removed += 1
        continue

    if tvg:
        seen_tvg.add(tvg)
    if stream_key:
        seen_stream.add(stream_key)

    if group != last_group:
        out.append('## ' + group)
        last_group = group
    out.extend(block)
    out.append('')
    kept += 1

PATH.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')
print('PUBLIC SPORTS YOUTUBE DEDUPE kept=', kept, 'removed=', removed)
