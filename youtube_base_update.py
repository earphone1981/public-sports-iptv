from pathlib import Path
import subprocess

COOKIES='youtube_cookies.txt'
M3U=Path('public_sports.m3u')

C=[]
def add(label,source,tvg,display,group,file=''):
    C.append(dict(label=label,source=source,tvg=tvg,display=display,group=group,file=file))

# existing fixed lives
add('ナミビア','https://www.youtube.com/watch?v=ydYDqZQpim8','youtube.namibia.live','🇳🇦 ナミビア LIVE','その他LIVE','namibia_live.m3u')
add('松山市クリーンセンター','https://www.youtube.com/watch?v=C0gpM_qIIl0','youtube.matsuyama.clean','♻️ 松山市クリーンセンター LIVE','その他LIVE','youtube_test.m3u')
add('松山空港','https://www.youtube.com/watch?v=CFh9z-6IeEE','youtube.matsuyama.airport','✈️ 松山空港 LIVE','その他LIVE','matsuyama_airport_live.m3u')
add('愛媛MP','https://www.youtube.com/@EhimeMandarinPirates/live','youtube.ehime.mp.home','⚾ 愛媛マンダリンパイレーツ HOME LIVE','野球LIVE')
add('大阪環状線','https://www.youtube.com/watch?v=HYQHcAqNBms','youtube.osaka.loop.live','🚃 大阪環状線 LIVE','その他LIVE')
add('淡路島モンキーセンター','https://www.youtube.com/watch?v=lsxYH2XQQCg','youtube.awaji.monkey.live','🐒 淡路島モンキーセンター LIVE','その他LIVE')
add('柴犬なつとこどもたち','https://www.youtube.com/watch?v=AqhaZl0fRYY','youtube.shiba.natsu.live','🐕 柴犬なつとこどもたち LIVE','その他LIVE')
add('新冠・馬カメラ','https://www.youtube.com/watch?v=1NtYMzERRxs','youtube.niikappu.horse.live','🐴 コノド・馬の映るお天気カメラ','その他LIVE')

boats=[
('桐生','UCT2pRt_me0tOA8B2sakEv7Q','boat.kiryu'),('戸田','UCoLCf3aVRMSukwetHfn1p1A','boat.toda'),('江戸川','UCpNAwETM_vPV2Skumzc_KMA','boat.edogawa'),('平和島','UCGExstl4XKMun5eY9V0zlSg','boat.heiwajima'),('多摩川','UC4lvZQUptR8m5VDSu49xCGQ','boat.tamagawa'),('浜名湖','UCGZig6i5JrZ33jjW2GG6Bzw','boat.hamanako'),('蒲郡','UCZhuyNQgLORLjgl8hlA7uHw','boat.gamagori'),('常滑','UCu9lPbAk1MosTGm2yQ4BapQ','boat.tokoname'),('津','UCEUXzh5FRxDneaLvv0YdEfQ','boat.tsu'),('三国','UCu-yP6WJQ0zcx5nmWhxvJEg','boat.mikuni'),('びわこ','UCLbcsJqsT5Qa1axpYcOBpmg','boat.biwako'),('住之江','UCW3AReETO-oDmEoE-m3i7dQ','boat.suminoe'),('尼崎','UC-vpH4QQKPwsqsbESOfNgZQ','boat.amagasaki'),('鳴門','UCd8rJfg7p8qsASOEIIwAinQ','boat.naruto'),('丸亀','UC2CWDMG18mpBGXkI9KHdACQ','boat.marugame'),('児島','UC6IrOXVuw6xXLl1qJqYUrsg','boat.kojima'),('宮島','UCxvYC6PPCsy2_p0tGuvIv5w','boat.miyajima'),('徳山','UCqyq1Dav7D5ztEl_ierxsjw','boat.tokuyama'),('下関','UCl-7IwVjJHzWUhqxz7hwY1w','boat.shimonoseki'),('若松','UCll--OtE3eJpzb4uwX8MX9A','boat.wakamatsu'),('芦屋','UC5BunThJ_eBJq5gz-DOaRLw','boat.ashiya'),('福岡','UCgyb8el3rLkg8i0bEMboQhA','boat.fukuoka'),('唐津','UCO6ycDxAk-5OHAiKc71gNSQ','boat.karatsu'),('大村','UCPLb9R1EIqxNBy8Qzcrz8Wg','boat.omura')]
for venue,ch,tvg in boats:
    add(venue+' 公式YouTube',f'https://www.youtube.com/channel/{ch}/live',tvg,f'📺 {venue} 公式YouTube LIVE','ボートレース YouTube LIVE')

def get_url(source):
    cmd=['yt-dlp','--js-runtimes','node','--cookies',COOKIES,'--extractor-args','youtube:player_client=default,web_safari','--no-playlist','--match-filter','is_live','--no-warnings','-f','95/best[protocol^=m3u8]/best','-g',source]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    urls=[x.strip() for x in p.stdout.splitlines() if x.strip().startswith(('http://','https://'))]
    return urls[0] if p.returncode==0 and urls else None

def ext(ch):
    return f'#EXTINF:-1 tvg-id="{ch["tvg"]}" tvg-name="{ch["label"]} LIVE" group-title="{ch["group"]}",{ch["display"]}'

results=[]
for ch in C:
    try:u=get_url(ch['source'])
    except Exception as e: print('ERR',ch['label'],e);u=None
    if u:
        results.append((ch,u)); print('OK',ch['label'])
        if ch['file']: Path(ch['file']).write_text('#EXTM3U\n'+ext(ch)+'\n'+u+'\n',encoding='utf-8')

lines=M3U.read_text(encoding='utf-8-sig').replace('\r\n','\n').split('\n')
# remove previous BASE generated entries by label/group
managed_labels={x['label'] for x in C}
out=[];i=0
while i<len(lines):
    line=lines[i]
    kill=False
    if line.startswith('#EXTINF:'):
        if any((f'tvg-name="{lab} LIVE"' in line or (lab+' 公式YouTube' in line)) for lab in managed_labels): kill=True
        if 'ボートレース YouTube LIVE' in line: kill=True
    if kill:
        i+=1
        while i<len(lines) and not lines[i].startswith('#EXTINF:') and not lines[i].startswith('## '): i+=1
        continue
    out.append(line);i+=1
while out and not out[-1].strip(): out.pop()
out+=['','# === BASE YOUTUBE LIVE ===']
for ch,u in results: out += [f'## {ch["group"]}',ext(ch),u,'']
M3U.write_text('\n'.join(out).rstrip()+'\n',encoding='utf-8')
