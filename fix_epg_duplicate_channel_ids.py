from pathlib import Path
import xml.etree.ElementTree as ET

EPG = Path('epg.xml')

# 同名の地方競馬と競輪を表示名で混同しないよう、
# 競輪側だけひらがな表示にする。
REQUIRED_CHANNELS = {
    'keirin.kawasaki': 'かわさきけいりん',
    'keirin.nagoya': 'なごやけいりん',
    'keirin.kochi': 'こうちけいりん',
    'chihou.kawasaki_keiba': '川崎けいば',
    'chihou.nagoya_keiba': '名古屋けいば',
    'chihou.kochi_keiba': '高知けいば',
}

root = ET.parse(EPG).getroot()

# 既存channel定義をidで管理
channels = {}
for ch in root.findall('channel'):
    cid = ch.get('id')
    if cid and cid not in channels:
        channels[cid] = ch

# programme より前へ不足channelを追加し、対象表示名も正規化
first_programme_index = next(
    (i for i, child in enumerate(list(root)) if child.tag == 'programme'),
    len(root),
)

added = 0
updated = 0
for channel_id, display_name in REQUIRED_CHANNELS.items():
    ch = channels.get(channel_id)
    if ch is None:
        ch = ET.Element('channel', id=channel_id)
        ET.SubElement(ch, 'display-name').text = display_name
        root.insert(first_programme_index, ch)
        first_programme_index += 1
        channels[channel_id] = ch
        added += 1
    else:
        dn = ch.find('display-name')
        if dn is None:
            dn = ET.SubElement(ch, 'display-name')
        if dn.text != display_name:
            dn.text = display_name
            updated += 1

# channel id重複検査
seen = set()
for ch in root.findall('channel'):
    cid = ch.get('id')
    if cid in seen:
        raise SystemExit(f'duplicate channel id: {cid}')
    seen.add(cid)

# 対象programmeのchannel idが必ず定義されていることを確認
for prog in root.findall('programme'):
    cid = prog.get('channel')
    if cid in REQUIRED_CHANNELS and cid not in seen:
        raise SystemExit(f'missing channel definition: {cid}')

tree = ET.ElementTree(root)
if hasattr(ET, 'indent'):
    ET.indent(tree, space='    ')
tree.write(EPG, encoding='utf-8', xml_declaration=True)

print(f'EPG duplicate-name channel fix: added={added} updated={updated}')
for cid, name in REQUIRED_CHANNELS.items():
    print('OK', cid, name)
