from pathlib import Path
import xml.etree.ElementTree as ET

EPG = Path('epg.xml')

REQUIRED_CHANNELS = {
    'keirin.kawasaki': '川崎けいりん',
    'keirin.nagoya': '名古屋けいりん',
    'keirin.kochi': '高知けいりん',
    'chihou.kawasaki_keiba': '川崎けいば',
    'chihou.nagoya_keiba': '名古屋けいば',
    'chihou.kochi_keiba': '高知けいば',
}

root = ET.parse(EPG).getroot()
existing = {ch.get('id') for ch in root.findall('channel')}

# programme より前に channel を追加
first_programme_index = next(
    (i for i, child in enumerate(list(root)) if child.tag == 'programme'),
    len(root),
)

added = 0
for channel_id, display_name in REQUIRED_CHANNELS.items():
    if channel_id in existing:
        continue
    ch = ET.Element('channel', id=channel_id)
    ET.SubElement(ch, 'display-name').text = display_name
    root.insert(first_programme_index, ch)
    first_programme_index += 1
    existing.add(channel_id)
    added += 1

# 同一channel idが重複していないことも確認
seen = set()
for ch in root.findall('channel'):
    cid = ch.get('id')
    if cid in seen:
        raise SystemExit(f'duplicate channel id: {cid}')
    seen.add(cid)

# 対象programmeのchannel idが必ず定義されているか確認
for prog in root.findall('programme'):
    cid = prog.get('channel')
    if cid in REQUIRED_CHANNELS and cid not in seen:
        raise SystemExit(f'missing channel definition: {cid}')

tree = ET.ElementTree(root)
if hasattr(ET, 'indent'):
    ET.indent(tree, space='    ')
tree.write(EPG, encoding='utf-8', xml_declaration=True)

print(f'EPG duplicate-name channel fix: added={added}')
for cid in REQUIRED_CHANNELS:
    print('OK', cid)
