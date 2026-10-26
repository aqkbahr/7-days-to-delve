from pathlib import Path
from datetime import datetime
import json,shutil,os,hashlib,zipfile
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05-complete';B=Path((A/'base.txt').read_text().strip());P=R/'playtest/BatchFiveComplete';M=R/'src/ZZZZZZZZZZZZDelveBatch05World';pointer=R/'dist/latest-first-forest-release.txt'
assert Path(pointer.read_text(encoding='utf-8-sig').strip())==B,'Baseline changed; reconcile'
assert json.loads((A/'static-validation.json').read_text())['result']=='PASS'
for f,m in {'native-world.txt':'[Batch05World] PASS','native-gear.txt':'[Batch05] PASS','native-stations.txt':'[StationProbe] PASS','native-storage.txt':'[Batch04] PASS','native-core.txt':'PASS: 617'}.items():
 text=(A/f).read_text(encoding='utf-8-sig');assert m in text and '] FAIL' not in text,f
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
for p in M.rglob('*'):
 if p.is_file() and p.suffix!='.cs':assert sha(p)==sha(P/'Mods'/M.name/p.relative_to(M)),p
data=Path((B/'save-data-location.txt').read_text(encoding='utf-8-sig').strip());save=data/'Saves/Allium-v0.10/ForestTest02';assert save.is_dir()
savehash={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()}
(A/'save-before.json').write_text(json.dumps(savehash,indent=2))
backup=A/('ForestTest02-before-batch5-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.zip')
with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
 for n in savehash:z.write(save/n,'ForestTest02/'+n)
with zipfile.ZipFile(backup) as z:assert z.testzip() is None
(A/'save-backup.txt').write_text(str(backup))
release=R/'dist'/('Delve-Batch05-Complete-'+datetime.now().strftime('%Y%m%d-%H%M%S'));release.mkdir()
manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
for e in manifest['files']:
 src=B/e['path'];dest=release/e['path'];dest.parent.mkdir(parents=True,exist_ok=True)
 if e['path'].startswith(('Mods/','Worlds/')):os.link(src,dest)
 else:shutil.copy2(src,dest)
shutil.copytree(M,release/'Mods'/M.name,ignore=shutil.ignore_patterns('*.cs'))
shutil.copy2(B/'BATCH-05.txt',release/'BATCH-05-ITEMS.txt')
for n in ['BATCH-05.txt','START-HERE.txt']:shutil.copy2(R/'docs/batch-five-complete.txt',release/n)
launcher=(release/'Play-Allium.ps1').read_text(encoding='utf-8-sig')
launcher=launcher.replace("param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')","param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[switch]$InstallOnly)")
launcher=launcher.replace('    $package=$PSScriptRoot',"    if(Get-Process -Name 7DaysToDie -ErrorAction SilentlyContinue){throw 'Close 7 Days to Die before installing or starting the Delve profile.'}\n    $package=$PSScriptRoot")
launcher=launcher.replace("Write-Host \"POI elevations corrected: select NEW GAME, Allium-v0.10, and a new save name.\"","Write-Host '7 DAYS TO DELVE - Batch 5 complete. Continue ForestTest02 on Allium-v0.10.'")
launcher=launcher.replace("    Start-Process -FilePath", "    if($InstallOnly){Write-Host 'Batch 5 installed; game left closed.'; return}\n    Start-Process -FilePath").replace('-GameName=ForestTest01','-GameName=ForestTest02')
(release/'Play-Allium.ps1').write_text(launcher,encoding='utf-8')
evidence=release/'Evidence/Batch05Complete';evidence.mkdir(parents=True)
for n in ['base.txt','static-validation.json','native-world.txt','native-gear.txt','native-stations.txt','native-storage.txt','native-core.txt','crates.json']:shutil.copy2(A/n,evidence/n)
shutil.copy2(M/'WorldChanges.cs',evidence/'WorldChanges.cs');shutil.copy2(R/'tools/forest/BatchFiveWorldProbe.cs',evidence/'BatchFiveWorldProbe.cs');shutil.copy2(P/'server.log',evidence/'server.log')
(release/'VALIDATION.txt').write_text((R/'docs/batch-five-complete.txt').read_text()+'\n\nITEMS ACCEPTANCE RETAINED\n'+(B/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
manifest.update(version='0.13.1-batch05-complete',name='7 Days to Delve - Batch 5 Complete')
manifest['files']=[dict(path=p.relative_to(release).as_posix(),sha256=sha(p)) for p in sorted(release.rglob('*')) if p.is_file() and p.name!='manifest.json']
(release/'manifest.json').write_text(json.dumps(manifest,indent=2))
assert Path(pointer.read_text(encoding='utf-8-sig').strip())==B,'Newer release selected'
(A/'release.txt').write_text(str(release))
# Promotion occurs after installation and package verification, not here.
print('Packaged: '+str(release));print('Verified save backup: '+str(backup))
