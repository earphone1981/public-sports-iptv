from pathlib import Path
from urllib.parse import quote
import datetime
import re
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
OUT = BASE / 'public_sports.m3u'
EPG = BASE / 'epg.xml'
RAW = 'https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main'
EPG_URL = RAW + '/epg.xml'
JST = datetime.timezone(datetime.timedelta(hours=9))

INPUTS = [
    ('競輪', BASE/'keirin_master.m3u'),
    ('地方競馬', BASE/'keiba_master.m3u'),
    ('オートレース', BASE/'autorace_master.m3u'),
    ('ボートレース', BASE/'boatrace_today.m3u'),
]

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
    lines = path.read_text(encoding='utf-8-sig', errors='replace').replace('\r\n','\n').replace('\r','\n').split('\n')
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


def parse_xmltv(value):
    m = re.match(r'(\d{14})\s*([+-]\d{4})?', str(value or '').strip())
    if not m:
        return None
    digits, off = m.groups()
    if off:
        return datetime.datetime.strptime(f'{digits} {off}', '%Y%m%d%H%M%S %z').astimezone(JST)
    return datetime.datetime.strptime(digits, '%Y%m%d%H%M%S').replace(tzinfo=JST)


def session_rank(text, start):
    t = str(text or '')
    # EPGに明示区分があれば最優先。
    if 'オーバーミッドナイト' in t or 'OVER MIDNIGHT' in t.upper(): return 4
    if 'ミッドナイト' in t or 'MIDNIGHT' in t.upper(): return 3
    if 'ナイター' in t or 'NIGHT' in t.upper(): return 2
    if 'モーニング' in t or 'MORNING' in t.upper(): return 0
    if 'デイ' in t or 'DAY' in t.upper(): return 1
    # 明示がない競技は最初の番組開始時刻で大分類。
    if start:
        h = start.hour
        if h < 10: return 0
        if h < 15: return 1
        if h < 20: return 2
        if h < 23: return 3
        return 4
    return 1


def today_order():
    """EPGから本日開催チャンネルを抽出し、
    モーニング→デイ→ナイター→ミッドナイト→オーバーミッドナイト順のキーを返す。
    非開催・準備中だけのチャンネルは対象外。
    """
    if not EPG.exists():
        return {}
    try:
        root = ET.parse(EPG).getroot()
    except Exception as e:
        print('EPG parse failed:', e)
        return {}

    today = datetime.datetime.now(JST).date()
    found = {}
    bad_words = ('本日非開催', '開催なし', 'データ取得準備中', '開催情報確認待ち')

    for p in root.findall('programme'):
        cid = p.get('channel','')
        if not cid.startswith(('keirin.','chihou.','keiba.','auto.','boat.')):
            continue
        start = parse_xmltv(p.get('start'))
        stop = parse_xmltv(p.get('stop'))
        if not start:
            continue
        # 早朝まで続くオーバーミッドナイトは前日開催扱いにしないため、
        # EPG上の本日開始番組を基準にする。
        if start.date() != today:
            continue
        title = p.findtext('title') or ''
        desc = p.findtext('desc') or ''
        text = title + ' ' + desc
        if any(w in text for w in bad_words):
            continue
        rank = session_rank(text, start)
        key = (rank, start)
        if cid not in found or key < found[cid]:
            found[cid] = key

    return found


def sorted_entries(path, order):
    entries = read_entries(path)
    indexed = list(enumerate(entries))
    def key(pair):
        idx, block = pair
        cid = attr(block[0], 'tvg-id')
        if cid in order:
            rank, start = order[cid]
            return (0, rank, start, idx)
        return (1, 99, datetime.datetime.max.replace(tzinfo=JST), idx)
    indexed.sort(key=key)
    return [block for _, block in indexed]


def append_file(out, label, path, seen_ids=None, seen_exact=None, order=None):
    entries = sorted_entries(path, order) if order is not None else read_entries(path)
    if not entries:
        print(label, '0 <-', path.name)
        return 0
    if seen_ids is None: seen_ids=set()
    if seen_exact is None: seen_exact=set()
    added=0
    last_group=None
    for block in entries:
        ext=block[0]
        tvg_id=attr(ext,'tvg-id')
        url=block[-1] if block else ''
        exact=(ext,url)
        if tvg_id:
            if tvg_id in seen_ids: continue
            seen_ids.add(tvg_id)
        else:
            if exact in seen_exact: continue
            seen_exact.add(exact)
        group=attr(ext,'group-title')
        if group and group != last_group:
            out.append('## '+group); last_group=group
        elif not group and last_group is None:
            out.append('## '+label); last_group=label
        out.extend(block); out.append(''); added += 1
    print(label, added, '<-', path.name)
    return added


def raw(filename):
    return RAW + '/' + quote(filename)


def main():
    out=[f'#EXTM3U url-tvg="{EPG_URL}"','']
    total=0
    order=today_order()
    print('本日開催並べ替え対象:', len(order), 'ch')

    for label,path in INPUTS:
        total += append_file(out,label,path,order=order)

    seen_youtube_ids=set(); seen_youtube_exact=set()
    for label,path in YOUTUBE_INPUTS:
        total += append_file(out,label,path,seen_youtube_ids,seen_youtube_exact)

    out.append('## 中央競馬')
    for tvg,name,display,filename in JRA:
        out += [f'#EXTINF:-1 tvg-id="{tvg}" tvg-name="{name}" group-title="中央競馬",{display}',raw(filename),'']
        total += 1

    OUT.write_text('\n'.join(out).rstrip()+'\n',encoding='utf-8')
    print('M3U一本化 完了:',total,'ch')
    print('本日開催順: モーニング -> デイ -> ナイター -> ミッドナイト -> オーバーミッドナイト -> 非開催')

if __name__ == '__main__':
    main()
