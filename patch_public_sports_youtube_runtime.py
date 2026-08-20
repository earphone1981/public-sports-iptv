from pathlib import Path

PATH = Path('public_sports_youtube_update.py')

text = PATH.read_text(encoding='utf-8')
old = """        urls = [x.strip() for x in p.stdout.splitlines() if x.strip().startswith(('http://','https://'))]\n        if p.returncode == 0 and len(urls) == 1:\n            return urls[0]\n"""
new = """        urls = [x.strip() for x in p.stdout.splitlines() if x.strip().startswith(('http://','https://'))]\n        if p.returncode == 0 and urls:\n            hls = next((u for u in urls if '.m3u8' in u or 'manifest' in u), None)\n            return hls or urls[0]\n"""

if old not in text:
    raise SystemExit('target get_url block not found; updater layout changed')

text = text.replace(old, new, 1)
PATH.write_text(text, encoding='utf-8')
print('patched public_sports_youtube_update.py: multi-URL yt-dlp output supported')
