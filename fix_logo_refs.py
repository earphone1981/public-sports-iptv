from pathlib import Path
import re

# 外部画像プロキシは一部IPTVアプリでロゴ読込に失敗するため廃止。
# 競輪の既存4件は元URLへ戻す。
PROXY_REPL = {
    'https://images.weserv.nl/?url=https%3A%2F%2Futsunomiya-keirin.jp%2Fimg%2Flogo.png&w=1024&h=300&fit=contain&bg=white&output=png': 'https://utsunomiya-keirin.jp/img/logo.png',
    'https://images.weserv.nl/?url=https%3A%2F%2Fwww.kawasakikeirin.com%2Fimages%2Flogo_kawasaki.png&w=1024&h=300&fit=contain&bg=white&output=png': 'https://www.kawasakikeirin.com/images/logo_kawasaki.png',
    'https://images.weserv.nl/?url=https%3A%2F%2Fwww.ogakikeirin.com%2Fcommon%2Fimages%2Flogos%2Flogo.png%3F20190412&w=1024&h=300&fit=contain&bg=white&output=png': 'https://www.ogakikeirin.com/common/images/logos/logo.png?20190412',
    'https://images.weserv.nl/?url=https%3A%2F%2Fi0.wp.com%2Fminchari.com%2Fwp-content%2Fuploads%2F2025%2F06%2Fkokura-keirin.png%3Fresize%3D1024%252C300%26ssl%3D1&w=1024&h=300&fit=contain&bg=white&output=png': 'https://i0.wp.com/minchari.com/wp-content/uploads/2025/06/kokura-keirin.png?resize=1024%2C300&ssl=1',
}

BOAT_LOGOS = {
    'boat.kiryu': 'kiryu.png',
    'boat.toda': 'toda.png',
    'boat.edogawa': 'edogawa.png',
    'boat.heiwajima': 'heiwajima.png',
    'boat.tamagawa': 'tamagawa.png',
    'boat.hamanako': 'hamanako.png',
    'boat.gamagori': 'gamagori.png',
    'boat.tokoname': 'tokoname.png',
    'boat.tsu': 'tsu.png',
    'boat.mikuni': 'mikuni.png',
    'boat.biwako': 'biwako.png',
    'boat.suminoe': 'suminoe.png',
    'boat.amagasaki': 'amagasaki.png',
    'boat.naruto': 'naruto.png',
    'boat.marugame': 'marugame.png',
    'boat.kojima': 'kojima.png',
    'boat.miyajima': 'miyajima.png',
    'boat.tokuyama': 'tokuyama.png',
    'boat.shimonoseki': 'shimonoseki.png',
    'boat.wakamatsu': 'wakamatsu.png',
    'boat.ashiya': 'ashiya.png',
    'boat.fukuoka': 'fukuoka.png',
    'boat.karatsu': 'karatsu.png',
    'boat.omura': 'omura.png',
}

BOAT_BASE = (
    'https://raw.githubusercontent.com/earphone1981/public-sports-iptv/main/'
    'public_sports_logos_github_43/boatrace_24_spaced_cut_1024/'
)


def fix_file(path: Path):
    if not path.exists():
        return 0, 0

    text = path.read_text(encoding='utf-8-sig')
    proxy_changed = 0
    for old, new in PROXY_REPL.items():
        if old in text:
            text = text.replace(old, new)
            proxy_changed += 1

    boat_changed = 0
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith('#EXTINF:'):
            continue

        m = re.search(r'tvg-id="([^"]+)"', line)
        if not m:
            continue

        tvg_id = m.group(1)
        filename = BOAT_LOGOS.get(tvg_id)
        if not filename:
            continue

        logo = BOAT_BASE + filename
        if 'tvg-logo="' in line:
            new_line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo}"', line, count=1)
        else:
            new_line = line.replace(' group-title=', f' tvg-logo="{logo}" group-title=', 1)

        if new_line != line:
            lines[i] = new_line
            boat_changed += 1

    path.write_text('\n'.join(lines) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
    return proxy_changed, boat_changed


for filename in ('boatrace_today.m3u', 'public_sports.m3u'):
    proxy_count, boat_count = fix_file(Path(filename))
    print(f'{filename}: proxy={proxy_count}, boat_logo={boat_count}')
