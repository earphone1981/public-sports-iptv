from pathlib import Path

# 外部画像プロキシは一部IPTVアプリでロゴ読込に失敗するため廃止。
# public_sports.m3u は各元ロゴURLをそのまま使用する。
P = Path('public_sports.m3u')
if not P.exists():
    raise SystemExit('public_sports.m3u not found')

text = P.read_text(encoding='utf-8-sig')
repl = {
    'https://images.weserv.nl/?url=https%3A%2F%2Futsunomiya-keirin.jp%2Fimg%2Flogo.png&w=1024&h=300&fit=contain&bg=white&output=png': 'https://utsunomiya-keirin.jp/img/logo.png',
    'https://images.weserv.nl/?url=https%3A%2F%2Fwww.kawasakikeirin.com%2Fimages%2Flogo_kawasaki.png&w=1024&h=300&fit=contain&bg=white&output=png': 'https://www.kawasakikeirin.com/images/logo_kawasaki.png',
    'https://images.weserv.nl/?url=https%3A%2F%2Fwww.ogakikeirin.com%2Fcommon%2Fimages%2Flogos%2Flogo.png%3F20190412&w=1024&h=300&fit=contain&bg=white&output=png': 'https://www.ogakikeirin.com/common/images/logos/logo.png?20190412',
    'https://images.weserv.nl/?url=https%3A%2F%2Fi0.wp.com%2Fminchari.com%2Fwp-content%2Fuploads%2F2025%2F06%2Fkokura-keirin.png%3Fresize%3D1024%252C300%26ssl%3D1&w=1024&h=300&fit=contain&bg=white&output=png': 'https://i0.wp.com/minchari.com/wp-content/uploads/2025/06/kokura-keirin.png?resize=1024%2C300&ssl=1',
}

changed = 0
for old, new in repl.items():
    if old in text:
        text = text.replace(old, new)
        changed += 1

P.write_text(text, encoding='utf-8')
print(f'IPTV logo proxy rollback: {changed}/4')
