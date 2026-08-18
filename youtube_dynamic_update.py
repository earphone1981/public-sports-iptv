from pathlib import Path
import json, subprocess

COOKIES='youtube_cookies.txt'
M3U=Path('public_sports.m3u')

KEIRIN={'函館':'keirin.hakodate','青森':'keirin.aomori','いわき平':'keirin.iwakitaira','弥彦':'keirin.yahiko','前橋':'keirin.maebashi','取手':'keirin.toride','宇都宮':'keirin.utsunomiya','大宮':'keirin.omiya','西武園':'keirin.seibuen','京王閣':'keirin.keiogatsu','立川':'keirin.tachikawa','松戸':'keirin.matsudo','川崎':'keirin.kawasaki','平塚':'keirin.hiratsuka','小田原':'keirin.odawara','伊東':'keirin.ito','伊東温泉':'keirin.ito','静岡':'keirin.shizuoka','名古屋':'keirin.nagoya','岐阜':'keirin.gifu','大垣':'keirin.ogaki','豊橋':'keirin.toyohashi','松阪':'keirin.matsusaka','四日市':'keirin.yokkaichi','富山':'keirin.toyama','福井':'keirin.fukui','奈良':'keirin.nara','岸和田':'keirin.kishiwada','和歌山':'keirin.wakayama','玉野':'keirin.tamano','広島':'keirin.hiroshima','防府':'keirin.hofu','高松':'keirin.takamatsu','小松島':'keirin.komatsushima','高知':'keirin.kochi','松山':'keirin.matsuyama','小倉':'keirin.kokura','久留米':'keirin.kurume','武雄':'keirin.takeo','佐世保':'keirin.sasebo','別府':'keirin.beppu','熊本':'keirin.kumamoto'}
BOAT={'桐生':'boat.kiryu','戸田':'boat.toda','江戸川':'boat.edogawa','平和島':'boat.heiwajima','多摩川':'boat.tamagawa','浜名湖':'boat.hamanako','蒲郡':'boat.gamagori','常滑':'boat.tokoname','津':'boat.tsu','三国':'boat.mikuni','びわこ':'boat.biwako','住之江':'boat.suminoe','尼崎':'boat.amagasaki','鳴門':'boat.naruto','丸亀':'boat.marugame','児島':'boat.kojima','宮島':'boat.miyajima','徳山':'boat.tokuyama','下関':'boat.shimonoseki','若松':'boat.wakamatsu','芦屋':'boat.ashiya','福岡':'boat.fukuoka','唐津':'boat.karatsu','大村':'boat.omura'}
HORSE={'大井':'keiba.oi','TCK':'keiba.oi','船橋':'keiba.funabashi','川崎':'keiba.kawasaki','浦和':'keiba.urawa','金沢':'keiba.kanazawa','笠松':'keiba.kasamatsu','名古屋':'keiba.nagoya','園田':'keiba.sonoda','姫路':'keiba.himeji','高知':'keiba.kochi','佐賀':'keiba.saga','盛岡':'keiba.morioka','水沢':'keiba.mizusawa','門別':'keiba.monbetsu','帯広':'keiba.obihiro','ばんえい':'keiba.obihiro'}
AUTO={'川口':'auto.kawaguchi','伊勢崎':'auto.isesaki','浜松':'auto.hamamatsu','山陽':'auto.sanyo','飯塚':'auto.iizuka'}

# fixed venue channels from the user's subscriptions; only current LIVE is emitted
FIXED=[
('立川','https://www.youtube.com/@%E7%AB%8B%E5%B7%9D%E3%83%A9%E3%82%A4%E3%83%96%E4%B8%AD%E7%B6%99/live',KEIRIN['立川'],'競輪 YouTube LIVE'),('前橋','https://www.youtube.com/@%E5%89%8D%E6%A9%8B%E7%AB%B6%E8%BC%AA%E5%A0%B4/live',KEIRIN['前橋'],'競輪 YouTube LIVE'),('高知競輪','https://www.youtube.com/@%E9%AB%98%E7%9F%A5%E7%AB%B6%E8%BC%AA%E3%81%A1%E3%82%83%E3%82%93%E3%81%AD%E3%82%8B%E5%85%AC%E5%BC%8F/live',KEIRIN['高知'],'競輪 YouTube LIVE'),('名古屋','https://www.youtube.com/@758keirin/live',KEIRIN['名古屋'],'競輪 YouTube LIVE'),('京王閣','https://www.youtube.com/@tokyokeiokaku/live',KEIRIN['京王閣'],'競輪 YouTube LIVE'),('松山競輪','https://www.youtube.com/@%E6%9D%BE%E5%B1%B1%E7%AB%B6%E8%BC%AA/live',KEIRIN['松山'],'競輪 YouTube LIVE'),('函館','https://www.youtube.com/@rinrin-hakodate-Keirin/live',KEIRIN['函館'],'競輪 YouTube LIVE'),('伊東温泉','https://www.youtube.com/@itokeirin/live',KEIRIN['伊東'],'競輪 YouTube LIVE'),('いわき平','https://www.youtube.com/@iwakitairakeirin/live',KEIRIN['いわき平'],'競輪 YouTube LIVE'),('静岡','https://www.youtube.com/@shizuokakeirin/live',KEIRIN['静岡'],'競輪 YouTube LIVE'),('四日市','https://www.youtube.com/@keirinyokkaichi104/live',KEIRIN['四日市'],'競輪 YouTube LIVE'),('佐世保','https://www.youtube.com/@%E5%85%AC%E5%BC%8F_%E4%BD%90%E4%B8%96%E4%BF%9D%E7%AB%B6%E8%BC%AA/live',KEIRIN['佐世保'],'競輪 YouTube LIVE'),('大垣','https://www.youtube.com/@ogakikeirin/live',KEIRIN['大垣'],'競輪 YouTube LIVE'),('別府','https://www.youtube.com/@beppukeirin136/live',KEIRIN['別府'],'競輪 YouTube LIVE'),('弥彦','https://www.youtube.com/@%E5%BC%A5%E5%BD%A6%E7%AB%B6%E8%BC%AA/live',KEIRIN['弥彦'],'競輪 YouTube LIVE'),('久留米','https://www.youtube.com/@%E4%B9%85%E7%95%99%E7%B1%B3%E3%81%91%E3%81%84%E3%82%8A%E3%82%93%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%AB%E5%85%AC%E5%BC%8F/live',KEIRIN['久留米'],'競輪 YouTube LIVE'),('熊本','https://www.youtube.com/@kumamotokeirin87/live',KEIRIN['熊本'],'競輪 YouTube LIVE'),('川崎競輪','https://www.youtube.com/@%E5%B7%9D%E5%B4%8E%E7%AB%B6%E8%BC%AA%E5%A0%B4%E5%85%AC%E5%BC%8F/live',KEIRIN['川崎'],'競輪 YouTube LIVE'),('武雄','https://www.youtube.com/@%E6%AD%A6%E9%9B%84%E7%AB%B6%E8%BC%AA-t9x/live',KEIRIN['武雄'],'競輪 YouTube LIVE'),('富山','https://www.youtube.com/@toyamakeirin/live',KEIRIN['富山'],'競輪 YouTube LIVE'),('豊橋','https://www.youtube.com/@%E7%AB%B6%E8%BC%AA%E5%A0%B4%E8%B1%8A%E6%A9%8B/live',KEIRIN['豊橋'],'競輪 YouTube LIVE'),('岐阜','https://www.youtube.com/@%E5%B2%90%E9%98%9C%E3%81%91%E3%81%84%E3%82%8A%E3%82%93/live',KEIRIN['岐阜'],'競輪 YouTube LIVE'),('小倉','https://www.youtube.com/@%E5%B0%8F%E5%80%89%E7%AB%B6%E8%BC%AA%E5%85%AC%E5%BC%8F%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%ABLIVE/live',KEIRIN['小倉'],'競輪 YouTube LIVE'),('和歌山','https://www.youtube.com/@wakayamakeirin/live',KEIRIN['和歌山'],'競輪 YouTube LIVE'),('小松島','https://www.youtube.com/@ponstarkomatsushima/live',KEIRIN['小松島'],'競輪 YouTube LIVE'),('高松','https://www.youtube.com/@takamatsu-keirin/live',KEIRIN['高松'],'競輪 YouTube LIVE'),('広島','https://www.youtube.com/@%E3%81%B2%E3%82%8D%E3%81%97%E3%81%BE%E3%81%91%E3%81%84%E3%82%8A%E3%82%93%E3%81%B4%E3%83%BC%E3%81%99%E3%81%91%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%AB-n8u/live',KEIRIN['広島'],'競輪 YouTube LIVE'),('玉野','https://www.youtube.com/@LIVE-zr9mi/live',KEIRIN['玉野'],'競輪 YouTube LIVE'),('福井','https://www.youtube.com/@fukuikeirin/live',KEIRIN['福井'],'競輪 YouTube LIVE'),('松阪','https://www.youtube.com/@matsusaka_keirin_LIVE/live',KEIRIN['松阪'],'競輪 YouTube LIVE'),('宇都宮','https://www.youtube.com/@UTSUNOMIYA500KEIRIN/live',KEIRIN['宇都宮'],'競輪 YouTube LIVE'),('取手','https://www.youtube.com/@torideBank/live',KEIRIN['取手'],'競輪 YouTube LIVE'),('岸和田','https://www.youtube.com/@%E3%83%96%E3%83%83%E3%82%AD%E3%83%BC%E3%82%B9%E3%82%BF%E3%82%B8%E3%82%A2%E3%83%A0%E5%B2%B8%E5%92%8C%E7%94%B0/live',KEIRIN['岸和田'],'競輪 YouTube LIVE'),('松戸','https://www.youtube.com/@%E6%9D%BE%E6%88%B8%E3%81%91%E3%81%84%E3%82%8A%E3%82%93/live',KEIRIN['松戸'],'競輪 YouTube LIVE'),('防府','https://www.youtube.com/@%E9%98%B2%E5%BA%9C%E3%81%91%E3%81%84%E3%82%8A%E3%82%93/live',KEIRIN['防府'],'競輪 YouTube LIVE'),
('園田・姫路','https://www.youtube.com/@sonodahimejiweb/live','keiba.sonoda','地方競馬 YouTube LIVE'),('大井','https://www.youtube.com/@tckkeiba/live',HORSE['大井'],'地方競馬 YouTube LIVE'),('金沢','https://www.youtube.com/@%E9%87%91%E6%B2%A2%E7%AB%B6%E9%A6%AC%E5%85%AC%E5%BC%8F%E3%83%81%E3%83%A3%E3%83%B3%E3%83%8D%E3%83%AB/live',HORSE['金沢'],'地方競馬 YouTube LIVE'),('岩手競馬','https://www.youtube.com/@IwateKeibaITV/live',HORSE['盛岡'],'地方競馬 YouTube LIVE'),('門別','https://www.youtube.com/@live2820/live',HORSE['門別'],'地方競馬 YouTube LIVE'),('川崎競馬','https://www.youtube.com/@%E5%85%AC%E5%BC%8F%E5%B7%9D%E5%B4%8E%E7%AB%B6%E9%A6%AC/live',HORSE['川崎'],'地方競馬 YouTube LIVE'),('佐賀','https://www.youtube.com/@sagakeibaofficial/live',HORSE['佐賀'],'地方競馬 YouTube LIVE'),('笠松','https://www.youtube.com/@%E7%AC%A0%E6%9D%BE%E3%81%91%E3%81%84%E3%81%B0%E3%83%AC%E3%83%BC%E3%82%B9%E6%98%A0%E5%83%8F%E9%85%8D%E4%BF%A1%E3%83%81%E3%83%A3/live',HORSE['笠松'],'地方競馬 YouTube LIVE'),('船橋','https://www.youtube.com/@funabashi-keiba/live',HORSE['船橋'],'地方競馬 YouTube LIVE'),('浦和','https://www.youtube.com/@%E6%B5%A6%E5%92%8C%E7%AB%B6%E9%A6%AC%E5%85%AC%E5%BC%8F/live',HORSE['浦和'],'地方競馬 YouTube LIVE'),('ばんえい','https://www.youtube.com/@%E3%81%B0%E3%82%93%E3%81%88%E3%81%84%E5%8D%81%E5%8B%9D%E5%85%AC%E5%BC%8F/live',HORSE['ばんえい'],'地方競馬 YouTube LIVE'),('高知競馬','https://www.youtube.com/@KeibaOrJp/live',HORSE['高知'],'地方競馬 YouTube LIVE')]

CROSS=[('華奈tube','https://www.youtube.com/@kana_tube/streams'),('WINTICKET','https://www.youtube.com/@winticket0402/streams'),('レディースインフォメーション','https://www.youtube.com/@%E3%83%AC%E3%83%87%E3%82%A3%E3%83%BC%E3%82%B9%E3%82%A4%E3%83%B3%E3%83%95%E3%82%A9%E3%83%A1%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3/streams'),('オッズパーク','https://www.youtube.com/@oddsparkcorp/streams'),('楽天競馬','https://www.youtube.com/@rakutenkeiba/streams'),('オートレース公式','https://www.youtube.com/@autofficial/streams')]

SEARCHES=[('松山市南クリーンセンター入口付近','ytsearch1:LIVE 松山市南クリーンセンター入口付近','youtube.matsuyama.south.clean','🏭 松山市南クリーンセンター入口付近 LIVE'),('FloRacing 24/7','ytsearch1:LIVE NOW FloRacing 24/7','youtube.floracing.live','🏁 FloRacing 24/7 LIVE'),('瀬戸大橋','ytsearch1:瀬戸大橋 ライブカメラ KBN','youtube.seto.bridge.live','🌉 瀬戸大橋 LIVE'),('京都駅','ytsearch1:Kyoto Station Live Cam JR京都駅 ライブカメラ','youtube.kyoto.station.live','🚉 京都駅 LIVE'),('松山市本町','ytsearch1:松山市本町 ライブカメラ 南海放送NEWS','youtube.matsuyama.honmachi.live','🏙 松山市本町 LIVE'),('白良浜','ytsearch1:白良浜 ライブカメラ Movie Shirahama-Town','youtube.shirahama.live','🏖 白良浜 LIVE'),('Katmai','ytsearch1:LIVE Katmai National Park explore.org','youtube.katmai.bears.live','🐻 Katmai National Park LIVE'),('Sea Otter','ytsearch1:Sea Otter Cam Vancouver Aquarium LIVE','youtube.seaotter.live','🦦 Sea Otter Cam LIVE'),('関西国際空港','ytsearch1:関西国際空港 KIX ライブカメラ LIVE','youtube.kix.live','✈️ 関西国際空港 LIVE'),('ウェザーニュース','ytsearch1:ライブ 最新天気ニュース ウェザーニュース','youtube.weathernews.live','☀️ ウェザーニュース LIVE'),('高校野球','ytsearch1:高校野球 夏 甲子園 LIVE','youtube.highschool.baseball.live','⚾ 高校野球 LIVE'),('能登鹿島駅','ytsearch1:能登鹿島駅周辺 ライブ 穴水町','youtube.noto.kashima.live','🚃 能登鹿島駅 LIVE'),('道後温泉','ytsearch1:道後温泉本館 ライブカメラ','youtube.dogo.live','♨️ 道後温泉本館 LIVE')]

def run(cmd,timeout=120): return subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
def get_url(source):
    p=run(['yt-dlp','--js-runtimes','node','--cookies',COOKIES,'--no-playlist','--match-filter','is_live','--no-warnings','-f','95/best[protocol^=m3u8]/best','-g',source])
    u=[x.strip() for x in p.stdout.splitlines() if x.strip().startswith(('http://','https://'))]
    return u[0] if p.returncode==0 and u else None

def live_items(src):
    p=run(['yt-dlp','--cookies',COOKIES,'--flat-playlist','--dump-json','--playlist-end','40',src],180)
    out=[]
    for ln in p.stdout.splitlines():
        try:j=json.loads(ln)
        except:continue
        if j.get('live_status')=='is_live' or j.get('is_live'):
            if j.get('id'):out.append((j.get('title') or '', 'https://www.youtube.com/watch?v='+j['id']))
    return out

def classify(title):
    t=title.upper()
    if any(x in t for x in ['競輪','KEIRIN','FⅠ','FII','F1','F2','モーニング','ミッドナイト']):
        for k,v in sorted(KEIRIN.items(),key=lambda x:-len(x[0])):
            if k in title:return v,'競輪 YouTube LIVE'
    if any(x in t for x in ['ボート','BOAT','ヴィーナス','レディース','クイーンズ']):
        for k,v in sorted(BOAT.items(),key=lambda x:-len(x[0])):
            if k in title:return v,'ボートレース YouTube LIVE'
    if any(x in t for x in ['競馬','KEIBA','ばんえい','門別','盛岡','水沢']):
        for k,v in sorted(HORSE.items(),key=lambda x:-len(x[0])):
            if k in title:return v,'地方競馬 YouTube LIVE'
    if any(x in t for x in ['オートレース','AUTORACE']):
        for k,v in AUTO.items():
            if k in title:return v,'オートレース YouTube LIVE'
    return None,None

def ext(tvg,name,group): return f'#EXTINF:-1 tvg-id="{tvg}" tvg-name="{name}" group-title="{group}",{name}'

E=[]
for label,src,tvg,grp in FIXED:
    try:u=get_url(src)
    except:u=None
    if u:E.append((tvg,f'📺 {label} 公式YouTube LIVE',grp,u));print('OK FIXED',label)

for provider,src in CROSS:
    try:items=live_items(src)
    except:items=[]
    for title,page in items:
        tvg,grp=classify(title)
        if not tvg: print('UNMAPPED',provider,title);continue
        try:u=get_url(page)
        except:u=None
        if u:E.append((tvg,f'📺 {provider}｜{title}',grp,u));print('OK CROSS',provider,title)

for label,src,tvg,name in SEARCHES:
    try:u=get_url(src)
    except:u=None
    if u:E.append((tvg,name,'その他LIVE',u));print('OK SEARCH',label)

text=M3U.read_text(encoding='utf-8-sig').replace('\r\n','\n')
start='# === DYNAMIC YOUTUBE LIVE START ===';end='# === DYNAMIC YOUTUBE LIVE END ==='
if start in text and end in text:text=text.split(start,1)[0].rstrip()+"\n"+text.split(end,1)[1].lstrip()
seen=set();uniq=[]
for e in E:
    k=(e[0],e[1],e[3])
    if k not in seen:seen.add(k);uniq.append(e)
block=['',start]
for tvg,name,grp,u in uniq:block += [f'## {grp}',ext(tvg,name,grp),u,'']
block += [end,'']
M3U.write_text(text.rstrip()+"\n"+'\n'.join(block),encoding='utf-8')
print('DYNAMIC LIVE COUNT',len(uniq))
