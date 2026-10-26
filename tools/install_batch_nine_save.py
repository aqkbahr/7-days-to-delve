"""Install verified region repairs without replacing character or campaign files."""
from pathlib import Path
import hashlib,json,shutil,zipfile,os,subprocess
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-09';N=Path((A/'release.txt').read_text().strip());B=Path((A/'base.txt').read_text().strip())
data=Path((N/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02';candidate=R/'playtest/BatchNine/Saves/Allium-v0.10/ForestTest02'
assert '7DaysToDie' not in subprocess.check_output(['tasklist','/FI','IMAGENAME eq 7DaysToDie.exe'],text=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
snapshot=lambda:{str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()}
before=json.loads((A/'save-before.json').read_text());assert snapshot()==before,'Live save changed; reconcile before installing'
with zipfile.ZipFile(A/'ForestTest02-before-batch09.zip') as z:assert z.testzip() is None
for e in json.loads((N/'manifest.json').read_text())['files']:
 assert sha(N/e['path']).upper()==e['sha256'],e['path']
 if e['path'].startswith('Mods/'):assert sha(data/e['path']).upper()==e['sha256'],('Installed mod mismatch',e['path'])
changed=[]
for p in (candidate/'Region').glob('*.7rg'):
 rel=str(p.relative_to(candidate));assert rel in before,('Unexpected generated region',rel)
 if sha(p)!=before[rel]:changed.append(rel)
assert 0<len(changed)<=4,changed
assert '[Batch09AllChunks] PASS' in (A/'native-allchunks.txt').read_text(encoding='utf-8-sig')
for n in changed:shutil.copy2(candidate/n,save/(n+'.batch09-stage'))
for n in changed:os.replace(save/(n+'.batch09-stage'),save/n)
after=snapshot();assert set(after)==set(before)
for n,h in before.items():assert after[n]==(sha(candidate/n) if n in changed else h),n
(R/'dist/active-playtest-release.json').write_text(json.dumps({'release':str(N),'version':'0.15.0-batch09'},indent=2))
for n in ['latest-first-forest-release.txt','latest-batch-nine-release.txt']:(R/'dist'/n).write_text(str(N)+'\n')
(R/'dist/previous-first-forest-release.txt').write_text(str(B)+'\n')
shutil.copy2(R/'tools/Play-First-Forest.next.ps1',R/'tools/Play-First-Forest.ps1')
shutil.copy2(N/'Mods/Delve/Delve.dll',R/'src/Delve/Delve.dll')
readme=R/'README.txt';text=readme.read_text(encoding='utf-8-sig').replace('CURRENT FIRST PLAYTEST','PREVIOUS PLAYTEST')
readme.write_text('CURRENT FIRST PLAYTEST - BATCH 9 / 0.15.0\nRun Play-First-Forest.cmd from D:\\Projects\\ChatGPT\\7 days to delve.\nContinue ForestTest02. See docs/batch-nine-playtest.txt for recovery and validation.\n\n'+text,encoding='utf-8')
result={'result':'PASS','release':str(N),'save':'ForestTest02','changed_regions':changed,'unchanged_save_files':len(before)-len(changed),'player_files_unchanged':True,'backup':str(A/'ForestTest02-before-batch09.zip'),'game_left_closed':True}
(A/'installation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
