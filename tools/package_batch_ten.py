from pathlib import Path
from datetime import datetime
import shutil,json,os,hashlib,zipfile
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-10';P=R/'playtest/BatchTen';B=Path((A/'base.txt').read_text().strip());M=R/'src/ZZZZZZZZZZZZZZZDelveBatch10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
required={'native-batch.txt':'[Batch10] PASS','native-stations.txt':'[StationProbe] PASS','grip-validation.txt':'PASS 7'}
for n,m in required.items():
 t=(A/n).read_text(encoding='utf-8-sig');assert m in t and '] FAIL' not in t,n
log=(P/'server.log').read_text(encoding='utf-8-sig');assert not any(s in log for s in ['Failed to patch','EXCEPTION: In load chunk','Dropping TE with',' EXC ','XML patch for','TileEntityComposite.read: Failed']), 'Final server log has content/load errors'
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
assert sha(Path('D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed/Assembly-CSharp.dll'))==manifest['gameAssemblySha256']
allowed={'Mods/Delve/Delve.dll','Mods/ZDelvePresentation/DelvePresentation.dll'}
for e in manifest['files']:
 assert sha(B/e['path'])==e['sha256'],('Baseline changed',e['path'])
 if e['path'].startswith(('Mods/','Worlds/')):
  candidate=P/e['path'].replace('Worlds/','GeneratedWorlds/',1);assert sha(candidate)==e['sha256'] or e['path'] in allowed,('Unexpected change',e['path'])
data=Path((B/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02'
assert {str(p.relative_to(save)):sha(p).lower() for p in save.rglob('*') if p.is_file()}==json.loads((A/'save-before.json').read_text()),'Live save changed'
with zipfile.ZipFile(A/'ForestTest02-before-batch10.zip') as z:assert z.testzip() is None
N=R/'dist'/('Delve-Batch10-'+datetime.now().strftime('%Y%m%d-%H%M%S'));N.mkdir()
for e in manifest['files']:
 rel=e['path'];dest=N/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if rel.startswith(('Mods/','Worlds/')):
  candidate=P/rel.replace('Worlds/','GeneratedWorlds/',1)
  if sha(candidate)==e['sha256']:os.link(B/rel,dest)
  else:shutil.copy2(candidate,dest)
 else:shutil.copy2(B/rel,dest)
shutil.copytree(M,N/'Mods'/M.name)
for n in ['START-HERE.txt','BATCH-10.txt']:shutil.copy2(R/'docs/current-playtest-batch.txt',N/n)
launch=(N/'Play-Allium.ps1').read_text(encoding='utf-8-sig').replace('Batch 9','Current update 0.16.0');(N/'Play-Allium.ps1').write_text(launch,encoding='utf-8')
evidence=N/'Evidence/Batch10';evidence.mkdir(parents=True)
for n in list(required)+['recipe-routing.json','crate-blocks.json']:shutil.copy2(A/n,evidence/n)
shutil.copy2(P/'server.log',evidence/'final-server.log')
(N/'VALIDATION.txt').write_text((R/'docs/current-playtest-batch.txt').read_text()+'\nPrevious validation history follows.\n'+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
manifest.update(name='7 Days to Delve - Current playtest update',version='0.16.0-batch10')
manifest['files']=[dict(path=p.relative_to(N).as_posix(),sha256=sha(p)) for p in sorted(N.rglob('*')) if p.is_file() and p.name!='manifest.json']
(N/'manifest.json').write_text(json.dumps(manifest,indent=2));(A/'release.txt').write_text(str(N));print(N)
