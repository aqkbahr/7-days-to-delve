from pathlib import Path
from datetime import datetime
import shutil,json,os,hashlib,zipfile
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-11';P=R/'playtest/BatchEleven';B=Path((A/'base.txt').read_text().strip());M=R/'src/ZZZZZZZZZZZZZZZZZDelveBatch11'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
required={'native-batch.txt':'[Batch11] PASS','native-stations.txt':'[StationProbe] PASS','native-storage.txt':'[Batch11Storage] PASS','native-summoning.txt':'PASS','native-regression.txt':'[Batch10] PASS','asset-validation.txt':'PASS'}
for n,m in required.items():
 t=(A/n).read_text(encoding='utf-8-sig');assert m in t and '] FAIL' not in t,n
log=(P/'server.log').read_text(encoding='utf-8-sig');assert not any(s in log for s in ['Failed to patch','EXCEPTION: In load chunk','Dropping TE with',' EXC ','XML patch for','TileEntityComposite.read: Failed']), 'Final server log has content/load errors'
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
assert sha(Path('D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed/Assembly-CSharp.dll'))==manifest['gameAssemblySha256']
allowed={'Mods/Delve/Delve.dll','Mods/ZDelvePresentation/DelvePresentation.dll','Mods/ZZZZZZZZZZZDelveBatch05/DelveBatchFive.dll'}
for e in manifest['files']:
 assert sha(B/e['path'])==e['sha256'],('Baseline changed',e['path'])
 if e['path'].startswith(('Mods/','Worlds/')):
  candidate=P/e['path'].replace('Worlds/','GeneratedWorlds/',1);assert sha(candidate)==e['sha256'] or e['path'] in allowed,('Unexpected change',e['path'])
data=Path((B/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02'
assert {str(p.relative_to(save)):sha(p).lower() for p in save.rglob('*') if p.is_file()}==json.loads((A/'save-before.json').read_text()),'Live save changed'
with zipfile.ZipFile(A/'ForestTest02-before-batch11.zip') as z:assert z.testzip() is None
for module in [M,R/'src/ZZZZZZZZZZZZZZZZZDelveSummoning']:
 for file in module.rglob('*'):
  if file.is_file():assert sha(file)==sha(P/'Mods'/module.name/file.relative_to(module)),('Untested module change',file)
N=R/'dist'/('Delve-Batch11-'+datetime.now().strftime('%Y%m%d-%H%M%S'));N.mkdir()
for e in manifest['files']:
 rel=e['path'];dest=N/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if rel.startswith(('Mods/','Worlds/')):
  candidate=P/rel.replace('Worlds/','GeneratedWorlds/',1)
  if sha(candidate)==e['sha256']:os.link(B/rel,dest)
  else:shutil.copy2(candidate,dest)
 else:shutil.copy2(B/rel,dest)
shutil.copytree(M,N/'Mods'/M.name)
S=R/'src/ZZZZZZZZZZZZZZZZZDelveSummoning';shutil.copytree(S,N/'Mods'/S.name)
shutil.copy2(R/'docs/summoning-playtest.txt',N/'SUMMONING.txt')
for n in ['START-HERE.txt','BATCH-11.txt']:shutil.copy2(R/'docs/batch-eleven-playtest.txt',N/n)
launch=(N/'Play-Allium.ps1').read_text(encoding='utf-8-sig').replace('Batch 9','Current update 0.17.0').replace('Current update 0.16.1','Current update 0.17.0');(N/'Play-Allium.ps1').write_text(launch,encoding='utf-8')
evidence=N/'Evidence/Batch11';evidence.mkdir(parents=True)
for n in list(required)+['content.json']:shutil.copy2(A/n,evidence/n)
shutil.copy2(P/'server.log',evidence/'final-server.log')
(N/'VALIDATION.txt').write_text((R/'docs/batch-eleven-playtest.txt').read_text()+'\nPrevious validation history follows.\n'+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
manifest.update(name='7 Days to Delve - Current playtest update',version='0.17.0-batch11')
manifest['files']=[dict(path=p.relative_to(N).as_posix(),sha256=sha(p)) for p in sorted(N.rglob('*')) if p.is_file() and p.name!='manifest.json']
(N/'manifest.json').write_text(json.dumps(manifest,indent=2));(A/'release.txt').write_text(str(N));print(N)
