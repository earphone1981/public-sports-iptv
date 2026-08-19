from pathlib import Path
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

COOKIES = 'youtube_cookies.txt'
OUT = Path('public_sports_youtube.m3u')
M3U = Path('public_sports.m3u')
UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1'
REF = 'https://www.youtube.com/'

CORE = [
    ('keirin_master.m3u', '競輪 YouTube LIVE', '競輪'),
    ('keiba_master.m3u', '地方競馬 YouTube LIVE', '競馬'),
    ('autorace_master.m3u', 'オートレース YouTube LIVE', 'オートレース'),
    ('boatrace_today.m3u', 'ボートレース YouTube LIVE', 'ボートレース'),
]

# 既知の公式チャンネル。未登録場は公式LIVE検索へフォールバックする。
DIRECT = {
    'keirin.tachikawa':'https://www.youtube.com/@%E7%AB%8B%E5%B7%9D%E3%83%A9%E3%82%A4%E3%83%96%E4%B8%AD%E7%B6%99/live',
    'keirin.maebashi':'https://www.youtube.com/@%E5%89%8D%E6%A9%8B%E7%AB%B6%E8%BC%AA%E5%A0%B4/live',
    'keirin.kochi':'https://www.youtube.com/@%E9%AB%98%E7%9F%A5%E7%AB%B6%E8%BC%AA%E3%81%A1%E3%82%83%E3%82%93%E3%81%AD%E3%82%8B%E5%85%AC%E5%BC%8F/live',
    'keirin.nagoya':'https://www.youtube.com/@758keirin/live',
    'keirin.keiogatsu':'https://www.youtube.com/@tokyokeiokaku/live',
    'keirin.matsuyama':'https://www.youtube.com/@%E6%9D%BE%E5%B1%B1%E7%AB%B6%E8%BC%AA/live',
    'keirin.hakodate':'https://www.youtube.com/@rinrin-hakodate-Keirin/live',
    'keirin.ito':'https://www.youtube.com/@itokeirin/live',
    'keirin.iwakitaira':'https://www.youtube.com/@iwakitairakeirin/live',
    'keirin.shizuoka':'https://www.youtube.com/@shizuokakeirin/live',
    'keirin.yokkaichi':'https://www.youtube.com/@keirinyokkaichi104/live',
    'keirin.sasebo':'https://www.youtube.com/@%E5%85%AC%E5%BC%8F_%E4%BD%90%E4%B8%96%E4%BF%9D%E7%AB%B6%E8%BC%AA/live',
    'keirin.ogaki':'https://www.youtube.com/@ogakikeirin/live',
    'keirin.beppu':'https://www.youtube.com/@beppukeirin136/live',
    'keirin.yahiko':'https://www.youtube.com/@%E5%BC%A5%E5%BD%A6%E7%AB%B6%E8%BC%AA/live',
    'keirin.kurume':'https://www.youtube.com/@%E4%B9%85%E7%95%99%E7%B1%B3%E3%81%91%E3%81%84%E3%82%8A%E3%82%93%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%AB%E5%85%AC%E5%BC%8F/live',
    'keirin.kumamoto':'https://www.youtube.com/@kumamotokeirin87/live',
    'keirin.kawasaki':'https://www.youtube.com/@%E5%B7%9D%E5%B4%8E%E7%AB%B6%E8%BC%AA%E5%A0%B4%E5%85%AC%E5%BC%8F/live',
    'keirin.takeo':'https://www.youtube.com/@%E6%AD%A6%E9%9B%84%E7%AB%B6%E8%BC%AA-t9x/live',
    'keirin.toyama':'https://www.youtube.com/@toyamakeirin/live',
    'keirin.toyohashi':'https://www.youtube.com/@%E7%AB%B6%E8%BC%AA%E5%A0%B4%E8%B1%8A%E6%A9%8B/live',
    'keirin.gifu':'https://www.youtube.com/@%E5%B2%90%E9%98%9C%E3%81%91%E3%81%84%E3%82%8A%E3%82%93/live',
    'keirin.kokura':'https://www.youtube.com/@%E5%B0%8F%E5%80%89%E7%AB%B6%E8%BC%AA%E5%85%AC%E5%BC%8F%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%ABLIVE/live',
    'keirin.wakayama':'https://www.youtube.com/@wakayamakeirin/live',
    'keirin.komatsushima':'https://www.youtube.com/@ponstarkomatsushima/live',
    'keirin.takamatsu':'https://www.youtube.com/@takamatsu-keirin/live',
    'keirin.hiroshima':'https://www.youtube.com/@%E3%81%B2%E3%82%8D%E3%81%97%E3%81%BE%E3%81%91%E3%81%84%E3%82%8A%E3%82%93%E3%81%B4%E3%83%BC%E3%81%99%E3%81%91%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%AB-n8u/live',
    'keirin.tamano':'https://www.youtube.com/@LIVE-zr9mi/live',
    'keirin.fukui':'https://www.youtube.com/@fukuikeirin/live',
    'keirin.matsusaka':'https://www.youtube.com/@matsusaka_keirin_LIVE/live',
    'keirin.utsunomiya':'https://www.youtube.com/@UTSUNOMIYA500KEIRIN/live',
    'keirin.toride':'https://www.youtube.com/@torideBank/live',
    'keirin.kishiwada':'https://www.youtube.com/@%E3%83%96%E3%83%83%E3%82%AD%E3%83%BC%E3%82%B9%E3%82%BF%E3%82%B8%E3%82%A2%E3%83%A0%E5%B2%B8%E5%92%8C%E7%94%B0/live',
    'keirin.matsudo':'https://www.youtube.com/@%E6%9D%BE%E6%88%B8%E3%81%91%E3%81%84%E3%82%8A%E3%82%93/live',
    'keirin.hofu':'https://www.youtube.com/@%E9%98%B2%E5%BA%9C%E3%81%91%E3%81%84%E3%82%8A%E3%82%93/live',
    'chihou.sonoda':'https://www.youtube.com/@sonodahimejiweb/live',
    'chihou.himeji':'https://www.youtube.com/@sonodahimejiweb/live',
    'chihou.oi':'https://www.youtube.com/@tckkeiba/live',
    'chihou.kanazawa':'https://www.youtube.com/@%E9%87%91%E6%B2%A2%E7%AB%B6%E9%A6%AC%E5%85%AC%E5%BC%8F%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%AB/live',
    'chihou.morioka':'https://www.youtube.com/@IwateKeibaITV/live',
    'chihou.mizusawa':'https://www.youtube.com/@IwateKeibaITV/live',
    'chihou.mombetsu':'https://www.youtube.com/@live2820/live',
    'chihou.kawasaki_keiba':'https://www.youtube.com/@%E5%85%AC%E5%BC%8F%E5%B7%9D%E5%B4%8E%E7%AB%B6%E9%A6%AC/live',
    'chihou.saga':'https://www.youtube.com/@sagakeibaofficial/live',
    'chihou.kasamatsu':'https://www.youtube.com/@%E7%AC%A0%E6%9D%BE%E3%81%91%E3%81%84%E3%81%B0%E3%83%AC%E3%83%BC%E3%82%B9%E6%98%A0%E5%83%8F%E9%85%8D%E4%BF%A1%E3%83%81%E3%83%A3/live',
    'chihou.funabashi':'https://www.youtube.com/@funabashi-keiba/live',
    'chihou.urawa':'https://www.youtube.com/@%E6%B5%A6%E5%92%8C%E7%AB%B6%E9%A6%AC%E5%85%AC%E5%BC%8F/live',
    'chihou.obihiro':'https://www.youtube.com/@%E3%81%B0%E3%82%93%E3%81%88%E3%81%84%E5%8D%81%E5%8B%9D%E5%85%AC%E5%BC%8F/live',
    'chihou.kochi_keiba':'https://www.youtube.com/@KeibaOrJp/live',
}

BOAT_CHANNELS = {
'boat.kiryu':'UCT2pRt_me0tOA8B2sakEv7Q','boat.toda':'UCoLCf3aVRMSukwetHfn1p1A','boat.edogawa':'UCpNAwETM_vPV2Skumzc_KMA','boat.heiwajima':'UCGExstl4XKMun5eY9V0zlSg','boat.tamagawa':'UC4lvZQUptR8m5VDSu49xCGQ','boat.hamanako':'UCGZig6i5JrZ33jjW2GG6Bzw','boat.gamagori':'UCZhuyNQgLORLjgl8hlA7uHw','boat.tokoname':'UCu9lPbAk1MosTGm2yQ4BapQ','boat.tsu':'UCEUXzh5FRxDneaLvv0YdEfQ','boat.mikuni':'UCu-yP6WJQ0zcx5nmWhxvJEg','boat.biwako':'UCLbcsJqsT5Qa1axpYcOBpmg','boat.suminoe':'UCW3AReETO-oDmEoE-m3i7dQ','boat.amagasaki':'UC-vpH4QQKPwsqsbESOfNgZQ','boat.naruto':'UCd8rJfg7p8qsASOEIIwAinQ','boat.marugame':'UC2CWDMG18mpBGXkI9KHdACQ','boat.kojima':'UC6IrOXVuw6xXLl1qJqYUrsg','boat.miyajima':'UCxvYC6PPCsy2_p0tGuvIv5w','boat.tokuyama':'UCqyq1Dav7D5ztEl_ierxsjw','boat.shimonoseki':'UCl-7IwVjJHzWUhqxz7hwY1w','boat.wakamatsu':'UCll--OtE3eJpzb4uwX8MX9A','boat.ashiya':'UC5BunThJ_eBJq5gz-DOaRLw','boat.fukuoka':'UCgyb8el3rLkg8i0bEMboQhA','boat.karatsu':'UCO6ycDxAk-5OHAiKc71gNSQ','boat.omura':'UCPLb9R1EIqxNBy8Qzcrz8Wg'}
for tvg, ch in BOAT_CHANNELS.items():
    DIRECT[tvg] = f'https://www.youtube.com/channel/{ch}/live'

CROSS = [
    ('WINTICKET','youtube.winticket.live','https://www.youtube.com/@winticket0402/live','WINTICKET 公式 LIVE'),
    ('オッズパーク','youtube.oddspark.live','https://www.youtube.com/@oddsparkcorp/live','オッズパーク 公式 LIVE'),
    ('チャリロト','youtube.chariloto.live',None,'チャリロト 公式 LIVE'),
    ('Kドリームス','youtube.kdreams.live',None,'Kドリームス 公式 LIVE'),
    ('ガールズインフォメーション','youtube.girls.info.live','https://www.youtube.com/@%E3%83%AC%E3%83%87%E3%82%A3%E3%83%BC%E3%82%B9%E3%82%A4%E3%83%B3%E3%83%95%E3%82%A9%E3%83%A1%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3/live','ガールズインフォメーション LIVE'),
]


def run(cmd, timeout=120):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def get_url(page):
    selectors = ['best[protocol^=m3u8][vcodec!=none][acodec!=none]','96/95/94/93/92/91','best[protocol^=m3u8]','best']
    for selector in selectors:
        p = run(['yt-dlp','--js-runtimes','node','--cookies',COOKIES,'--extractor-args','youtube:player_client=default,web_safari','--no-playlist','--match-filter','is_live','--no-warnings','-f',selector,'-g',page], 120)
        urls = [x.strip() for x in p.stdout.splitlines() if x.strip().startswith(('http://','https://'))]
        if p.returncode == 0 and len(urls) == 1:
            return urls[0]
    return None


def search_live(query):
    p = run(['yt-dlp','--cookies',COOKIES,'--flat-playlist','--dump-json','--playlist-end','5',f'ytsearch5:{query}'], 90)
    pages = []
    for line in p.stdout.splitlines():
        try:
            item = json.loads(line)
        except Exception:
            continue
        vid = item.get('id')
        if vid:
            pages.append(f'https://www.youtube.com/watch?v={vid}')
    for page in pages:
        try:
            u = get_url(page)
        except Exception:
            u = None
        if u:
            return u
    return None


def parse_master(path, group, keyword):
    rows = []
    text = Path(path).read_text(encoding='utf-8-sig', errors='replace') if Path(path).exists() else ''
    for line in text.splitlines():
        if not line.startswith('#EXTINF:'):
            continue
        mid = re.search(r'tvg-id="([^"]+)"', line)
        mname = re.search(r'tvg-name="([^"]+)"', line)
        mlogo = re.search(r'tvg-logo="([^"]+)"', line)
        if not mid or not mname:
            continue
        tvg = mid.group(1)
        name = mname.group(1)
        clean = re.sub(r'（.*?）','',name)
        clean = re.sub(r'^(BOATRACE)','',clean)
        clean = clean.replace('けいりん','').replace('けいば','').replace('オート','').strip()
        rows.append(dict(tvg=tvg,name=name,venue=clean,logo=mlogo.group(1) if mlogo else '',group=group,keyword=keyword))
    return rows


def resolve(row):
    source = DIRECT.get(row['tvg'])
    try:
        url = get_url(source) if source else search_live(f"{row['venue']} {row['keyword']} 公式 LIVE")
    except Exception as e:
        print('ERR', row['name'], e)
        url = None
    if not url:
        print('NO LIVE', row['name'])
        return None
    print('OK', row['name'])
    return row, url


def ext(row):
    logo = f' tvg-logo="{row["logo"]}"' if row.get('logo') else ''
    return f'#EXTINF:-1 tvg-id="{row["tvg"]}" tvg-name="{row["name"]} 公式YouTube LIVE"{logo} group-title="{row["group"]}",📺 {row["name"]} 公式YouTube LIVE'

rows = []
for p,g,k in CORE:
    rows.extend(parse_master(p,g,k))

results = []
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(resolve, r) for r in rows]
    for f in as_completed(futs):
        r = f.result()
        if r:
            results.append(r)

# 同じ公式チャンネルを共有する場は、検索結果URLが同じなら1本に整理。
seen_url = set()
unique = []
for row, url in sorted(results, key=lambda x: (x[0]['group'], x[0]['name'])):
    if url in seen_url:
        continue
    seen_url.add(url)
    unique.append((row,url))

for label,tvg,source,query in CROSS:
    try:
        url = get_url(source) if source else search_live(query)
    except Exception as e:
        print('ERR CROSS', label, e)
        url = None
    if url:
        row = dict(tvg=tvg,name=label,logo='',group='公営競技 横断LIVE')
        unique.append((row,url))
        print('OK CROSS',label)
    else:
        print('NO LIVE CROSS',label)

lines = ['#EXTM3U','']
for row,url in unique:
    lines += [f'## {row["group"]}', ext(row), f'#EXTVLCOPT:http-referrer={REF}', f'#EXTVLCOPT:http-user-agent={UA}', url, '']
OUT.write_text('\n'.join(lines).rstrip()+'\n', encoding='utf-8')
print('PUBLIC SPORTS YOUTUBE LIVE COUNT', len(unique))

# public_sports.m3uにも即反映。後続のmerge/normalizeでもOUTから再構築できる。
if M3U.exists():
    text = M3U.read_text(encoding='utf-8-sig').replace('\r\n','\n')
    start = '# === PUBLIC SPORTS YOUTUBE LIVE START ==='
    end = '# === PUBLIC SPORTS YOUTUBE LIVE END ==='
    if start in text and end in text:
        text = text.split(start,1)[0].rstrip()+'\n'+text.split(end,1)[1].lstrip()
    out = text.rstrip()+f'\n\n{start}\n'+ '\n'.join(lines[2:]).rstrip()+f'\n{end}\n'
    M3U.write_text(out, encoding='utf-8')
