from pathlib import Path
from datetime import datetime
import json,shutil,os,hashlib
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-08';B=Path((A/'base.txt').read_text().strip());P=R/'playtest/BatchEight';M=R/'src/ZZZZZZZZZZZZZDelveBatch08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
for f,marker in {'native-build.txt':'[Batch08Build] PASS','native-assets.txt':'[Batch08] PASS','native-attributes.txt':'[Batch08Attributes] PASS','native-stations.txt':'[StationProbe] PASS','native-storage.txt':'[Batch04] PASS','native-save-reload.txt':'[Batch08Save] PASS apply=False','native-gear.txt':'[Batch08Gear] PASS'}.items():
 t=(A/f).read_text(encoding='utf-8-sig');assert marker in t and '] FAIL' not in t,f
assert json.loads((A/'static-validation.json').read_text())['result']=='PASS'
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'));allowed={'Mods/Delve/Delve.dll'}|{e['path'] for e in manifest['files'] if '/delve_wayrest_forest.' in e['path']}
for e in manifest['files']:
 assert sha(B/e['path'])==e['sha256'],('Baseline changed',e['path'])
 if e['path'].startswith(('Mods/','Worlds/')):
  path=P/e['path'].replace('Worlds/','GeneratedWorlds/',1)
  assert sha(path)==e['sha256'] or e['path'] in allowed,('Unexpected candidate change',e['path'])
release=R/'dist'/('Delve-Batch08-'+datetime.now().strftime('%Y%m%d-%H%M%S'));release.mkdir()
for e in manifest['files']:
 rel=e['path'];dest=release/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if rel.startswith(('Mods/','Worlds/')):
  candidate=P/rel.replace('Worlds/','GeneratedWorlds/',1)
  if sha(candidate)==e['sha256']:os.link(B/rel,dest)
  else:shutil.copy2(candidate,dest)
 else:shutil.copy2(B/rel,dest)
shutil.copytree(M,release/'Mods'/M.name)
for n in ['START-HERE.txt','BATCH-08.txt']:shutil.copy2(R/'docs/batch-eight-playtest.txt',release/n)
launcher=(release/'Play-Allium.ps1').read_text(encoding='utf-8-sig').replace('Batch 5 complete','Batch 8').replace('Batch 5 installed','Batch 8 installed');(release/'Play-Allium.ps1').write_text(launcher,encoding='utf-8')
evidence=release/'Evidence/Batch08';evidence.mkdir(parents=True)
for file in A.glob('*.txt'):shutil.copy2(file,evidence/file.name)
for n in ['static-validation.json','furnishings.xml']:shutil.copy2(A/n,evidence/n)
for n in ['BatchEightProbe.cs','BatchEightAttributes.cs','BatchEightGearProbe.cs']:shutil.copy2(R/'tools/forest'/n,evidence/n)
shutil.copy2(P/'Mods/StationProbe/wayrest-changes.xml',evidence/'wayrest-changes.xml');shutil.copy2(P/'server.log',evidence/'restart-server.log')
for n in ['progression-results.txt','progression-ui-results.txt']:shutil.copy2(R/'artifacts/tests'/n,evidence/n)
manifest.update(name='7 Days to Delve - Batch 8',version='0.14.0-batch08')
manifest['files']=[dict(path=p.relative_to(release).as_posix(),sha256=sha(p)) for p in sorted(release.rglob('*')) if p.is_file() and p.name!='manifest.json']
(release/'manifest.json').write_text(json.dumps(manifest,indent=2));(A/'release.txt').write_text(str(release));print(release)
