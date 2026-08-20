from pathlib import Path

PATH = Path('public_sports_youtube_update.py')
text = PATH.read_text(encoding='utf-8')

# 1) yt-dlp が映像/音声など複数URLを返しても成功扱いにする。
old = """        urls = [x.strip() for x in p.stdout.splitlines() if x.strip().startswith(('http://','https://'))]\n        if p.returncode == 0 and len(urls) == 1:\n            return urls[0]\n"""
new = """        urls = [x.strip() for x in p.stdout.splitlines() if x.strip().startswith(('http://','https://'))]\n        if p.returncode == 0 and urls:\n            hls = next((u for u in urls if '.m3u8' in u or 'manifest' in u), None)\n            return hls or urls[0]\n"""
if old in text:
    text = text.replace(old, new, 1)

# 2) 公式チャンネル /live が未来の予約LIVEを返した場合、
#    現在LIVE中の動画を検索して再試行する。
old_resolve = """        url = get_url(source) if source else search_live(f\"{row['venue']} {row['keyword']} 公式 LIVE\")\n"""
new_resolve = """        url = get_url(source) if source else None\n        if not url:\n            url = search_live(f\"{row['venue']} {row['keyword']} 公式 LIVE\")\n"""
if old_resolve not in text:
    raise SystemExit('resolve target block not found; updater layout changed')
text = text.replace(old_resolve, new_resolve, 1)

# 3) WINTICKET等の横断公式も /live が予約枠なら検索へフォールバック。
old_cross = """        url = get_url(source) if source else search_live(query)\n"""
new_cross = """        url = get_url(source) if source else None\n        if not url:\n            url = search_live(query)\n"""
if old_cross not in text:
    raise SystemExit('cross target block not found; updater layout changed')
text = text.replace(old_cross, new_cross, 1)

PATH.write_text(text, encoding='utf-8')
print('patched public_sports_youtube_update.py: multi-URL + active-LIVE search fallback enabled')
