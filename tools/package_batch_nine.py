from pathlib import Path
from datetime import datetime
import shutil,json,os,hashlib
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-09';P=R/'playtest/BatchNine';B=Path((A/'base.txt').read_text().strip());M=R/'src/ZZZZZZZZZZZZZZDelveBatch09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
required={'native-nutrition.txt':'[Batch09] PASS','native-forage.txt':'[Batch09Forage] PASS','native-recovery.txt':'restored=4 stations=10','native-reload.txt':'mode=reload restored=0 stations=10','native-allchunks.txt':'[Batch09AllChunks] PASS','native-stations-final.txt':'[StationProbe] PASS','native-attributes.txt':'[Batch08Attributes] PASS','native-gear.txt':'[Batch08Gear] PASS','native-storage.txt':'[Batch04] PASS'}
required['native-activation.txt']='[Batch09Activation] PASS'
for n,m in required.items():
 t=(A/n).read_text(encoding='utf-8-sig');assert m in t and '] FAIL' not in t,n
assert json.loads((A/'static-validation.json').read_text())['result']=='PASS'
log=(P/'server.log').read_text(encoding='utf-8-sig');assert not any(s in log for s in ['Failed to patch','EXCEPTION: In load chunk','Dropping TE with',' EXC ','XML patch for','TileEntityComposite.read: Failed']), 'Final server log has content/load errors'
api=Path('D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed/Assembly-CSharp.dll');api_sha=(A/'game-api-sha256.txt').read_text().strip().upper();assert sha(api)==api_sha
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
allowed={'Mods/Delve/Delve.dll','Mods/ZZZZZZZZZZZZDelveBatch05World/DelveBatchFiveWorld.dll'}|{f'Mods/ZZZZDelveBatch02/Config/{n}.xml' for n in ['items','recipes','loot','traders','quests','challenges','blocks']}
for e in manifest['files']:
 assert sha(B/e['path'])==e['sha256'],('Baseline changed',e['path'])
 if e['path'].startswith(('Mods/','Worlds/')):
  candidate=P/e['path'].replace('Worlds/','GeneratedWorlds/',1);assert sha(candidate)==e['sha256'] or e['path'] in allowed,('Unexpected change',e['path'])
N=R/'dist'/('Delve-Batch09-'+datetime.now().strftime('%Y%m%d-%H%M%S'));N.mkdir()
for e in manifest['files']:
 rel=e['path'];dest=N/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 if rel.startswith(('Mods/','Worlds/')):
  candidate=P/rel.replace('Worlds/','GeneratedWorlds/',1)
  if sha(candidate)==e['sha256']:os.link(B/rel,dest)
  else:shutil.copy2(candidate,dest)
 else:shutil.copy2(B/rel,dest)
shutil.copytree(M,N/'Mods'/M.name)
for n in ['START-HERE.txt','BATCH-09.txt']:shutil.copy2(R/'docs/batch-nine-playtest.txt',N/n)
verify=(N/'Verify-Package.ps1').read_text(encoding='utf-8-sig');verify="param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')\n"+verify
verify=verify.replace('foreach($entry in $manifest.files)',"$api=Join-Path $GamePath '7DaysToDie_Data/Managed/Assembly-CSharp.dll'\nif(!$manifest.gameAssemblySha256 -or (Get-FileHash -LiteralPath $api -Algorithm SHA256).Hash -ne $manifest.gameAssemblySha256){throw 'The installed game binaries differ from this tested Delve build. Stop for a compatibility update before loading the save.'}\nforeach($entry in $manifest.files)")
(N/'Verify-Package.ps1').write_text(verify,encoding='utf-8')
launch=(N/'Play-Allium.ps1').read_text(encoding='utf-8-sig').replace('Batch 8','Batch 9').replace("& (Join-Path $package 'Verify-Package.ps1')","& (Join-Path $package 'Verify-Package.ps1') -GamePath $GamePath").replace('installed 7 Days to Die 3.3 folder','installed 7 Days to Die 3.4 folder')
(N/'Play-Allium.ps1').write_text(launch,encoding='utf-8')
evidence=N/'Evidence/Batch09';evidence.mkdir(parents=True)
for n in list(required)+['native-audit.txt','native-records-audit.txt','native-records-repair.txt','static-validation.json','firearm-34-rebase.json','game-api-sha256.txt']:shutil.copy2(A/n,evidence/n)
shutil.copy2(P/'server.log',evidence/'final-server.log')
for n in ['BatchNineProbe.cs','BatchNineForageProbe.cs']:shutil.copy2(R/'tools/forest'/n,evidence/n)
shutil.copy2(R/'src/Code/FirstTierCrafting.cs',evidence/'FirstTierCrafting.cs');shutil.copy2(R/'src/ZZZZZZZZZZZZDelveBatch05World/WorldChanges.cs',evidence/'WorldChanges.cs')
(N/'VALIDATION.txt').write_text((R/'docs/batch-nine-playtest.txt').read_text()+'\nPrevious test history follows; the game target is now 3.4 b6.\n'+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
manifest.update(name='7 Days to Delve - Batch 9',version='0.15.0-batch09',gameVersion='3.4.0 (b6)',gameAssemblySha256=api_sha)
manifest['files']=[dict(path=p.relative_to(N).as_posix(),sha256=sha(p)) for p in sorted(N.rglob('*')) if p.is_file() and p.name!='manifest.json']
(N/'manifest.json').write_text(json.dumps(manifest,indent=2));(A/'release.txt').write_text(str(N));print(N)

