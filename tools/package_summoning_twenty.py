from pathlib import Path
from datetime import datetime
import hashlib,json,os,shutil,zipfile
R=Path(__file__).resolve().parents[1];A=R/'artifacts/summoning-20';P=R/'playtest/Summoning20';B=Path((A/'base.txt').read_text().strip());M=R/'src/ZZZZZZZZZZZZZZZZZZDelveSummoning20'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
evidence=R/'artifacts/validation/summoning20'
for name,marker in {'talents':'PASS 310','regression':'PASS 42','batch11':'[Batch11] PASS','combined':'[Batch10] PASS','stations':'[StationProbe] PASS'}.items():
 t=(evidence/(name+'.txt')).read_text();assert marker in t and 'FAIL' not in t,name
assert (A/'content-validation.txt').read_text().startswith('PASS:')
log=(P/'server.log').read_text(encoding='utf-8-sig');assert not any(s in log for s in ['Failed to patch','EXCEPTION: In load chunk','Dropping TE with',' EXC ','XML patch for','TileEntityComposite.read: Failed']), 'Server load error'
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
assert sha(Path('D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed/Assembly-CSharp.dll'))==manifest['gameAssemblySha256']
for e in manifest['files']:
 assert sha(B/e['path'])==e['sha256'],('Baseline changed',e['path'])
 if e['path'].startswith(('Mods/','Worlds/')):
  candidate=P/e['path'].replace('Worlds/','GeneratedWorlds/',1)
  assert sha(candidate)==e['sha256'] or e['path']=='Mods/Delve/Delve.dll',('Unexpected change',e['path'])
assert sha(A/'Delve.dll')==sha(P/'Mods/Delve/Delve.dll')
for f in M.rglob('*'):
 if f.is_file():assert sha(f)==sha(P/'Mods'/M.name/f.relative_to(M))
data=Path((B/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02'
assert {str(p.relative_to(save)):sha(p).lower() for p in save.rglob('*') if p.is_file()}==json.loads((A/'save-before.json').read_text()),'Live save changed'
with zipfile.ZipFile(A/'ForestTest02-before.zip') as z:assert z.testzip() is None
N=R/'dist'/('Delve-Summoning20-'+datetime.now().strftime('%Y%m%d-%H%M%S'));N.mkdir()
for e in manifest['files']:
 rel=e['path'];dest=N/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if rel=='Mods/Delve/Delve.dll':shutil.copy2(A/'Delve.dll',dest)
 elif rel.startswith(('Mods/','Worlds/')):os.link(B/rel,dest)
 else:shutil.copy2(B/rel,dest)
shutil.copytree(M,N/'Mods'/M.name)
notes=(R/'docs/summoning-twenty-playtest.txt').read_text()
(N/'SUMMONING20.txt').write_text(notes)
(N/'START-HERE.txt').write_text(notes+'\nPrevious combined-build notes:\n'+(B/'START-HERE.txt').read_text(encoding='utf-8-sig'))
(N/'VALIDATION.txt').write_text('Summoning20: 310 new native checks, 42 summoning regression checks, 10563 Batch11 checks, 1386 Batch10 checks, 9821 station checks and 625 loaded definitions passed. Live UI and multiplayer acceptance remain for playtesting.\n\n'+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'))
launch=(N/'Play-Allium.ps1').read_text(encoding='utf-8-sig').replace('0.17.0','0.18.0');(N/'Play-Allium.ps1').write_text(launch,encoding='utf-8')
E=N/'Evidence/Summoning20';shutil.copytree(evidence,E);shutil.copy2(A/'content-validation.txt',E);shutil.copy2(P/'server.log',E/'final-server.log')
manifest.update(name='7 Days to Delve - Summoning through rank 20',version='0.18.0-summoning20')
manifest['files']=[dict(path=p.relative_to(N).as_posix(),sha256=sha(p)) for p in sorted(N.rglob('*')) if p.is_file() and p.name!='manifest.json']
(N/'manifest.json').write_text(json.dumps(manifest,indent=2));(A/'release.txt').write_text(str(N));print(N)
