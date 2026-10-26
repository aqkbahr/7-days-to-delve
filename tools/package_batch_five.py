"""Promote only the exact frozen combined build accepted by the native fixtures."""
from pathlib import Path
from datetime import datetime
import json,hashlib,shutil,os,csv
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05';B=Path((A/'base.txt').read_text(encoding='utf-8-sig').strip());P=R/'playtest/BatchFive';M=R/'src/ZZZZZZZZZZZDelveBatch05'
pointer=R/'dist/latest-first-forest-release.txt'
assert Path(pointer.read_text(encoding='utf-8-sig').strip())==B,'Selected release changed; reconcile before promoting'
assert json.loads((A/'static-validation.json').read_text())['result']=='PASS'
for file,markers in {'native-gear.txt':['[Batch05] PASS'],'native-stations.txt':['[StationProbe] PASS','254 recipe variants','PASS: 617'],'native-storage.txt':['[Batch04] PASS'],'persistence-check.txt':['[MatPersistence] PASS check 1'],'persistence-seed-server.log':['[MatPersistence] PASS seed 1']}.items():
 text=(A/file).read_text(encoding='utf-8-sig')
 for marker in markers:assert marker in text,(file,marker)
 if not file.endswith('server.log'):assert '] FAIL' not in text,file
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
for e in manifest['files']:
 assert sha(B/e['path'])==e['sha256'].upper(),('baseline changed',e['path'])
 if e['path'].startswith(('Mods/','Worlds/')):assert sha(P/e['path'].replace('Worlds/','GeneratedWorlds/',1))==e['sha256'].upper(),('test profile mismatch',e['path'])
for file in M.rglob('*'):
 if file.is_file() and file.suffix!='.cs':assert sha(file)==sha(P/'Mods'/M.name/file.relative_to(M)),file
release=R/'dist'/('Delve-Batch05-'+datetime.now().strftime('%Y%m%d-%H%M%S'));release.mkdir()
for e in manifest['files']:
 src=B/e['path'];dst=release/e['path'];dst.parent.mkdir(parents=True,exist_ok=True)
 if e['path'].startswith(('Mods/','Worlds/')):
  try:os.link(src,dst)
  except OSError:shutil.copy2(src,dst)
 else:shutil.copy2(src,dst)
shutil.copytree(M,release/'Mods'/M.name,ignore=shutil.ignore_patterns('*.cs'))
shutil.copy2(A/'catalogue.json',release/'Catalogue/first-playtest.json')
for name in ['START-HERE.txt','BATCH-05.txt']:shutil.copy2(R/'docs/batch-five-playtest.txt',release/name)
labels={}
for file in [Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config/Localization.csv')]+sorted((release/'Mods').glob('*/Config/Localization.csv')):
 with file.open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   if row.get('Key') and row.get('english'):labels[row['Key']]=row['english']
catalog=json.loads((A/'catalogue.json').read_text());alias={a:b for b,s in catalog['station_bases'].items() for a in s['aliases']}
guide=['BATCH 5 CURRENT CRAFTING CATALOGUE','Starter equipment: Field Crafting Mat; no add-ons. Primitive gear and field supplies: inventory.','Specialist stations retain proficiency 10/20 add-ons. Alchemy-40 excavation charge stays gated.','Costs below are per recipe batch. See BATCH-05.txt for balance and save compatibility.','']
for row in sorted(catalog['recipes'],key=lambda r:(r['rank'],r['skill'] or '',labels.get(r['name'],r['name']))):
 station=alias.get(row['station'],row['station']);place=labels.get(station,station) if station else 'Inventory'
 if row.get('tool'):place+=' + '+labels.get(row['tool'],row['tool'])
 guide.append(f"P{row['rank']} {row['skill'] or 'Supplies'}: {row['count']} {labels.get(row['name'],row['name'])} | {place} | "+', '.join(f'{v} {labels.get(k,k)}' for k,v in row['ingredients'].items()))
for name in ['CRAFTING-STATIONS.txt','Catalogue/forest-ready-catalogue.txt']:(release/name).write_text('\n'.join(guide)+'\n',encoding='utf-8')
for name in ['STATION-UPGRADES.txt','CRAFTING-GUIDE.txt','M3-EQUIPMENT-SPELLS.txt','M3-PLAYTEST.txt']:
 path=release/name
 if path.exists():path.write_text('BATCH 5 UPDATE: All Delve starter equipment now uses the Field Crafting Mat. See BATCH-05.txt for current costs/stats and CRAFTING-STATIONS.txt for current recipes. Earlier starter-equipment figures below are historical. Specialist add-on requirements remain.\n\n'+path.read_text(encoding='utf-8-sig'),encoding='utf-8')
validation='''BATCH 5 - FIELD CRAFTING MAT ACCEPTANCE
PASS: 254 recipe variants (253 through proficiency 20 and the retained rank-40 charge).
PASS: all 25 starter equipment recipes are mat-exclusive; primitive gear and
field supplies remain portable. All costs increase, with no later-stage dependencies.
PASS: native starter/Forged armor, normalized melee damage and durability,
native rune-hit damage, mending capacity, actual mat asset and collider geometry.
PASS: 9,571 station checks across 254 recipes, 94 add-on queues and 27 station
variants; native missing/wrong/installed/removed add-ons and disk/network serialization.
PASS: 617 core checks (starter assertions updated to this balance) and 51 Batch 04 checks.
PASS: placed mat identity, stored output and exact queued recipe survive an actual
server restart; the saved queue completes correctly after reload.
The mat has output-only workstation modules and no tool-grid window/add-on slots.
The woven mesh and icon were built and previewed in Unity; the game loads the asset.
Baseline Mods/Worlds are unchanged and every shipped module matches the test profile.
Tests use an isolated save. Hands-on visual fit, progression pacing and multiplayer
acceptance remain playtest work. See Evidence/Batch05 for exact results.

Historical acceptance follows; previous starter-equipment balance is superseded.

'''
(release/'VALIDATION.txt').write_text(validation+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
dest=release/'Evidence/Batch05';dest.mkdir(parents=True)
for name in ['base.txt','static-validation.json','changes.json','checks.xml','native-gear.txt','native-stations.txt','native-storage.txt','persistence-seed-server.log','persistence-check.txt','final-server.log']:shutil.copy2(A/name,dest/name)
for file in M.glob('*.cs'):shutil.copy2(file,dest/file.name)
shutil.copy2(A/'art/Preview/delveFieldCraftingMat.png',dest/'mat-preview.png')
shutil.copy2(A/'art/result.txt',dest/'art-validation.txt')
manifest.update(version='0.13.0-batch05',name='Allium Batch 5 - Field Crafting Mat')
manifest['files']=[dict(path=p.relative_to(release).as_posix(),sha256=sha(p)) for p in sorted(release.rglob('*')) if p.is_file() and p!=release/'manifest.json']
(release/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for e in manifest['files']:assert sha(release/e['path'])==e['sha256'],e['path']
assert Path(pointer.read_text(encoding='utf-8-sig').strip())==B,'Newer release selected during packaging'
(R/'dist/previous-first-forest-release.txt').write_text(str(B)+'\n')
for file in (R/'dist').glob('latest-*-release.txt'):
 if Path(file.read_text(encoding='utf-8-sig').strip())==B:file.write_text(str(release)+'\n')
(R/'dist/latest-batch-five-release.txt').write_text(str(release)+'\n');pointer.write_text(str(release)+'\n')
(A/'release.txt').write_text(str(release));print('PASS packaged, verified and selected: '+str(release))
