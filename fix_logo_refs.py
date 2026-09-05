from pathlib import Path
import re

BOAT_LOGOS = {
    'boat.kiryu':'kiryu.png','boat.toda':'toda.png','boat.edogawa':'edogawa.png','boat.heiwajima':'heiwajima.png','boat.tamagawa':'tamagawa.png','boat.hamanako':'hamanako.png','boat.gamagori':'gamagori.png','boat.tokoname':'tokoname.png','boat.tsu':'tsu.png','boat.mikuni':'mikuni.png','boat.biwako':'biwako.png','boat.suminoe':'suminoe.png','boat.amagasaki':'amagasaki.png','boat.naruto':'naruto.png','boat.marugame':'marugame.png','boat.kojima':'kojima.png','boat.miyajima':'miyajima.png','boat.tokuyama':'tokuyama.png','boat.shimonoseki':'shimonoseki.png','boat.wakamatsu':'wakamatsu.png','boat.ashiya':'ashiya.png','boat.fukuoka':'fukuoka.png','boat.karatsu':'karatsu.png','boat.omura':'omura.png'
}
KEIRIN_LOGOS = {
    'keirin.hakodate':'hakodate.png','keirin.aomori':'aomori.png','keirin.iwakitaira':'iwakitaira.png','keirin.yahiko':'yahiko.png','keirin.maebashi':'maebashi.png','keirin.toride':'toride.png','keirin.utsunomiya':'utsunomiya.png','keirin.omiya':'omiya.png','keirin.seibuen':'seibuen.png','keirin.keiogatsu':'keiokaku.png','keirin.tachikawa':'tachikawa.png','keirin.matsudo':'matsudo.png','keirin.kawasaki':'kawasaki.png','keirin.hiratsuka':'hiratsuka.png','keirin.odawara':'odawara.png','keirin.ito':'ito.png','keirin.shizuoka':'shizuoka.png','keirin.nagoya':'nagoya.png','keirin.gifu':'gifu.png','keirin.ogaki':'ogaki.png','keirin.toyohashi':'toyohashi.png','keirin.toyama':'toyama.png','keirin.matsusaka':'matsusaka.png','keirin.yokkaichi':'yokkaichi.png','keirin.fukui':'fukui.png','keirin.nara':'nara.png','keirin.mukomachi':'mukomachi.png','keirin.wakayama':'wakayama.png','keirin.kishiwada':'kishiwada.png','keirin.tamano':'tamano.png','keirin.hiroshima':'hiroshima.png','keirin.hofu':'hofu.png','keirin.takamatsu':'takamatsu.png','keirin.komatsushima':'komatsushima.png','keirin.kochi':'kochi.png','keirin.matsuyama':'matsuyama.png','keirin.kokura':'kokura.png','keirin.kurume':'kurume.png','keirin.takeo':'takeo.png','keirin.sasebo':'sasebo.png','keirin.beppu':'beppu.png','keirin.kumamoto':'kumamoto.png','keirin.pist6':'pist6.png'
}
JRA_LOGOS = {
    'jra.gch':'gch.png',
    'jra.east':'east_web3.png',
    'jra.west':'west_web4.png',
    'jra.hokkaido':'hokkaido_local.png',
}
ROOT='https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main/public_sports_logos_github_43/'
REPO_ROOT='https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main/'
BOAT_BASE=ROOT+'boatrace_24_spaced_cut_1024/'
KEIRIN_BASE=ROOT+'keirin_square_final_43/'

def fix_file(path):
    p=Path(path)
    if not p.exists(): return 0
    text=p.read_text(encoding='utf-8-sig')
    lines=text.splitlines(); changed=0
    for i,line in enumerate(lines):
        if not line.startswith('#EXTINF:'): continue
        m=re.search(r'tvg-id="([^"]+)"',line)
        if not m: continue
        tid=m.group(1); logo=None
        if tid in BOAT_LOGOS: logo=BOAT_BASE+BOAT_LOGOS[tid]
        elif tid in KEIRIN_LOGOS: logo=KEIRIN_BASE+KEIRIN_LOGOS[tid]
        elif tid in JRA_LOGOS: logo=REPO_ROOT+JRA_LOGOS[tid]
        if not logo: continue
        if 'tvg-logo="' in line:
            new=re.sub(r'tvg-logo="[^"]*"',f'tvg-logo="{logo}"',line,count=1)
        else:
            new=line.replace(' group-title=',f' tvg-logo="{logo}" group-title=',1)
        if new!=line: lines[i]=new; changed+=1
    p.write_text('\n'.join(lines)+('\n' if text.endswith('\n') else ''),encoding='utf-8')
    return changed

for fn in ('keirin_master.m3u','boatrace_today.m3u','public_sports.m3u'):
    print(f'{fn}: logo_changed={fix_file(fn)}')
