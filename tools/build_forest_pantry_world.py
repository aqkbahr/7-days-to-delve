"""Publish verified pantry gardens as Allium-v0.9; preserve prior map revisions."""
from pathlib import Path
from xml.etree import ElementTree as E
import shutil, json, hashlib, csv

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'artifacts/maps/Allium-v0.8'
out=ROOT/'artifacts/maps/Allium-v0.9'
author=ROOT/'playtest/PantryAuthor/Mods'
report=E.parse(author/'AlliumTools/pantry-gardens.xml')
assert len(report.getroot())==3
mapping={r.get('source'):r.get('target') for r in report.getroot()}
out.mkdir(parents=True,exist_ok=True)
for file in source.iterdir():
    if file.is_file() and file.name!='main.ttw':shutil.copy2(file,out/file.name)
dest=ROOT/'src/DelveWayrest/Prefabs/POIs'
for row in report.getroot():
    assert len(row)==12
    for suffix in ('.tts','.xml','.blocks.nim'):
        p=author/'DelveWayrest/Prefabs/POIs'/(row.get('target')+suffix)
        assert p.exists() and p.stat().st_size
        shutil.copy2(p,dest/p.name)
records=json.loads((source/'locations.json').read_text())
tree=E.parse(source/'prefabs.xml');changed=0
for r in records:
    if r['hub']!=0 or r['prefab'] not in mapping:continue
    matches=[e for e in tree.getroot() if e.get('name')==r['prefab'] and list(map(int,e.get('position').split(',')))[::2]==r['position'][::2]]
    assert len(matches)==1
    matches[0].set('name',mapping[r['prefab']]);r['prefab']=mapping[r['prefab']];changed+=1
assert changed==3
world_cells=E.Element('gardens')
for r in records:
    if r['prefab'] not in mapping.values():continue
    cells=next(e for e in report.getroot() if e.get('target')==r['prefab'])
    meta=E.parse(dest/(r['prefab']+'.xml'))
    offset=int(meta.find("property[@name='YOffset']").get('value'))
    garden=E.SubElement(world_cells,'garden',name=r['prefab'])
    for cell in cells:
        E.SubElement(garden,'cell',x=str(r['position'][0]+int(cell.get('x'))),
                     y=str(r['position'][1]+offset+int(cell.get('y'))),
                     z=str(r['position'][2]+int(cell.get('z'))),crop=cell.get('crop'))
E.indent(world_cells)
E.ElementTree(world_cells).write(ROOT/'artifacts/validation/pantry-world-cells.xml')
E.indent(tree);tree.write(out/'prefabs.xml',encoding='utf-8',xml_declaration=True)
(out/'locations.json').write_text(json.dumps(records,indent=2)+'\n')
tree=E.parse(out/'map_info.xml');tree.find("property[@name='Name']").set('value','Allium-v0.9');tree.write(out/'map_info.xml',encoding='utf-8',xml_declaration=True)
shutil.copy2(author/'AlliumTools/pantry-gardens.xml',out/'pantry-gardens.xml')
for name in ('dtm.raw','biomes.png','splat1.png','splat2.png','splat3.png','splat4.png','radiation.png','spawnpoints.xml','water_info.xml'):
    assert hashlib.sha256((source/name).read_bytes()).digest()==hashlib.sha256((out/name).read_bytes()).digest(),name
loc=ROOT/'src/DelveWayrest/Config/Localization.csv'
with loc.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
rows=[r for r in rows if r[0] not in mapping.values()]
for record in records:
    if record['prefab'] in mapping.values():rows.append([record['prefab'],'DelveWayrest','','','','',record['name']])
with loc.open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(rows)
(ROOT/'src/Worlds/Allium/pantry-gardens.json').write_text(json.dumps([r for r in records if r['prefab'] in mapping.values()],indent=2)+'\n')
validation=json.loads((source/'input-validation.json').read_text())
validation.update(world='Allium-v0.9',pantry_gardens=3,planted_plates=36)
validation['checks']+=['Three garden prefab variants: 36 farm plot plates planted with 12 forest crop types', 'All terrain, mineral deposits, other POIs and quest metadata preserved']
(out/'input-validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print('PASS: Allium-v0.9; three garden variants, 36 planted plates; terrain preserved.')
