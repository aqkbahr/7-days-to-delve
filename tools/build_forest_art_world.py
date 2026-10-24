"""Publish native-serialized Forest variants into a new map; preserve older worlds."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'artifacts/maps/Allium-v0.5'
out = ROOT / 'artifacts/maps/Allium-v0.6'
author = ROOT / 'playtest/ForestArtAuthor/Mods'
dest = ROOT / 'src/DelveWayrest/Prefabs/POIs'
native = Path('D:/Steam/steamapps/common/7 Days To Die/Data/Prefabs/POIs')
report = E.parse(author / 'AlliumTools/forest-art-report.xml')
entries = list(report.getroot())
assert len(entries) == 16
mapping = {e.get('source'): e.get('target') for e in entries}
out.mkdir(parents=True, exist_ok=True)
for file in source.iterdir():
    if file.is_file() and file.name != 'main.ttw':
        shutil.copy2(file, out / file.name)

def canonical(node):
    return node.tag, sorted(node.attrib.items()), (node.text or '').strip(), [canonical(c) for c in node]

def properties(root):
    return [canonical(p) for p in root if p.get('name') not in ('ExcludeDistantPOIMesh', 'EditorGroups')]

for e in entries:
    old, new = e.get('source'), e.get('target')
    original = (dest if old.startswith('delve_') else native) / (old + '.xml')
    converted = author / 'DelveWayrest/Prefabs/POIs'
    # Compare parsed properties, insensitive to native XML formatting.
    a = E.parse(original).getroot()
    b = E.parse(converted / (new + '.xml')).getroot()
    assert properties(a) == properties(b), old + ': gameplay metadata changed'
    for suffix in ('.tts', '.xml', '.blocks.nim'):
        file = converted / (new + suffix)
        assert file.is_file() and file.stat().st_size > 0
        shutil.copy2(file, dest / file.name)

records = json.loads((source / 'locations.json').read_text())
tree = E.parse(source / 'prefabs.xml')
changed = 0
for r in records:
    if r['hub'] != 0:
        continue
    old = r['prefab']
    assert old in mapping, old
    # Match position as well as source: other biomes reuse some native POIs.
    nodes = [p for p in tree.getroot() if p.get('name') == old
             and [int(v) for v in p.get('position').split(',')][::2] == r['position'][::2]]
    assert len(nodes) == 1, old
    nodes[0].set('name', mapping[old])
    r['prefab'] = mapping[old]
    changed += 1
assert changed == 16 and len(records) == 32
E.indent(tree)
tree.write(out / 'prefabs.xml', encoding='utf-8', xml_declaration=True)
(out / 'locations.json').write_text(json.dumps(records, indent=2))
tree = E.parse(source / 'map_info.xml')
tree.find("property[@name='Name']").set('value', 'Allium-v0.6')
tree.write(out / 'map_info.xml', encoding='utf-8', xml_declaration=True)

localization = ROOT / 'src/DelveWayrest/Config/Localization.csv'
with localization.open(newline='', encoding='utf-8-sig') as stream:
    rows = list(csv.reader(stream))
rows = [r for r in rows if r[0] not in mapping.values()]
rows += [[r['prefab'], 'DelveWayrest', '', '', '', '', r['name']]
         for r in records if r['hub'] == 0]
with localization.open('w', newline='', encoding='utf-8') as stream:
    csv.writer(stream).writerows(rows)

unchanged = ['dtm.raw', 'biomes.png', 'splat1.png', 'splat2.png', 'splat3.png',
             'splat4.png', 'radiation.png', 'spawnpoints.xml', 'water_info.xml']
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for name in unchanged:
    assert digest(source / name) == digest(out / name), name
validation = json.loads((source / 'input-validation.json').read_text())
assert validation['result'] == 'PASS'
validation.update(world='Allium-v0.6', forest_art_variants=16, new_block_definitions=0,
    painted_cells=sum(int(e.get('painted')) for e in entries),
    replacement_parents=sum(int(e.get('replaced')) for e in entries),
    serialization_verified_cells=sum(int(e.get('verifiedCells')) for e in entries))
validation['checks'] += ['Terrain, roads, water and spawns byte-identical to validated v0.5',
    '16 native prefab variants preserve all gameplay XML properties',
    '32 placements retained; only 16 Forest prefab IDs changed',
    'Every converted cell and paint value round-tripped through native serializer']
validation['limits'] = 'Headless validation only. Human visual inspection, walking, quest rally/reset and multiplayer playthrough remain pending. Ordinary replacement containers use native replacement loot tables.'
(out / 'input-validation.json').write_text(json.dumps(validation, indent=2))
shutil.copy2(author / 'AlliumTools/forest-art-report.xml', out / 'forest-art-report.xml')
print(json.dumps(validation, indent=2))
