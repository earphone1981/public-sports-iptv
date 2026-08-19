from pathlib import Path
from urllib.parse import quote
import re

BASE = Path(__file__).resolve().parent
OUT = BASE / 'public_sports.m3u'
RAW = 'https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main'
EPG_URL = RAW + '/epg.xml'

INPUTS = [
    ('競輪', BASE/'keirin_master.m3u'),
    ('地方競馬', BASE/'keiba_master.m3u'),
    ('オートレース', BASE/'autorace_master.m3u'),
    ('ボートレース', BASE/'boatrace_today.m3u'),
]

# 公営側は公営公式YouTubeのみ統合する。
# かなチューブ・一般LIVEは himitsu 側で管理するため、ここでは読まない。
YOUTUBE_INPUTS = [
    ('公営YouTube', BASE/'public_sports_youtube.m3u'),
]

JRA = [
    ('jra.gch','グリーンチャンネル','グリーンチャンネル（高画質）','gchmain.m3u8'),
    ('jra.gch','グリーンチャンネル','グリーンチャンネル（低画質）','gchmain_LQ.m3u8'),
    ('jra.east','JRA EAST','JRA EAST（高画質）','EAST_test.m3u8'),
    ('jra.east','JRA EAST','JRA EAST（低画質）','EAST_test_LQ.m3u8'),
    ('jra.west','JRA WEST','JRA WEST（高画質）','WEST_master .m3u8'),
    ('jra.west','JRA WEST','JRA WEST（低画質）','WEST_master_LQ.m3u8'),
    ('jra.hokkaido','JRA HOKKAIDO','JRA HOKKAIDO（高画質）','hokaido_master (1).m3u8'),
    ('jra.hokkaido','JRA HOKKAIDO','JRA HOKKAIDO（低画質）','hokaido_master_LQ.m3u8'),
]


def read_entries(path):
    if not path.exists():
        return []
    lines = path.read_text(encoding='utf-8-sig', errors='replace').replace('\r\n','\n').split('\n')
    entries=[]
    i=0
    while i < len(lines):
        line=lines[i].strip()
        if line.startswith('#EXTINF:'):
            block=[line]
            j=i+1
            url=False
            while j < len(lines):
                s=lines[j].strip()
                if not s:
                    j+=1; continue
                if s.startswith('#EXTINF:') or s.startswith('## '):
                    break
                if s.startswith('#'):
                    block.append(s); j+=1; continue
                block.append(s); url=True; j+=1; break
            if url:
                entries.append(block)
            i=j
            continue
        i+=1
    return entries


def attr(ext, name):
    m = re.search(rf'{re.escape(name)}="([^"]*)"', ext)
    return m.group(1).strip() if m else ''


def append_file(out, label, path, seen_ids=None, seen_exact=None):
    entries=read_entries(path)
    if not entries:
        print(label, '0 <-', path.name)
        return 0

    if seen_ids is None:
        seen_ids=set()
    if seen_exact is None:
        seen_exact=set()

    added=0
    last_group=None
    for block in entries:
        ext=block[0]
        tvg_id=attr(ext,'tvg-id')
        url=block[-1] if block else ''
        exact=(ext,url)

        if tvg_id:
            if tvg_id in seen_ids:
                continue
            seen_ids.add(tvg_id)
        else:
            if exact in seen_exact:
                continue
            seen_exact.add(exact)

        group=attr(ext,'group-title')
        if group and group != last_group:
            out.append('## '+group)
            last_group=group
        elif not group and last_group is None:
            out.append('## '+label)
            last_group=label
        out.extend(block)
        out.append('')
        added += 1

    print(label, added, '<-', path.name)
    return added


def raw(filename):
    return RAW + '/' + quote(filename)


def main():
    out=[f'#EXTM3U url-tvg="{EPG_URL}"','']
    total=0

    for label,path in INPUTS:
        total += append_file(out,label,path)

    seen_youtube_ids=set()
    seen_youtube_exact=set()
    for label,path in YOUTUBE_INPUTS:
        total += append_file(out,label,path,seen_youtube_ids,seen_youtube_exact)

    out.append('## 中央競馬')
    for tvg,name,display,filename in JRA:
        out += [f'#EXTINF:-1 tvg-id="{tvg}" tvg-name="{name}" group-title="中央競馬",{display}',raw(filename),'']
        total += 1

    OUT.write_text('\n'.join(out).rstrip()+'\n',encoding='utf-8')
    print('M3U一本化 完了:',total,'ch')
    print('YouTube重複防止: canonical source rebuild + tvg-id dedupe')

if __name__ == '__main__':
    main()
