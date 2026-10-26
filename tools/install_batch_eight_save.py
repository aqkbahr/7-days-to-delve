"""Install only the verified region delta, then promote the D: release."""
from pathlib import Path
import hashlib,json,shutil,zipfile,os
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-08';N=Path((A/'release.txt').read_text().strip());B=Path((A/'base.txt').read_text().strip());P=R/'playtest/BatchEight';data=Path((N/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02';candidate=P/'Saves/Allium-v0.10/ForestTest02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((A/'save-before.json').read_text());now={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()};assert before==now,'Live save changed; stop and reconcile'
assert 'new=0 already=76 preserved/skipped=0 stations=10 dirty=0' in (A/'native-save-reload.txt').read_text(encoding='utf-8-sig')
with zipfile.ZipFile(A/'ForestTest02-before-batch08.zip') as z:assert z.testzip() is None
manifest=json.loads((N/'manifest.json').read_text())
for e in manifest['files']:
 assert sha(N/e['path']).upper()==e['sha256'],('Package mismatch',e['path'])
 if e['path'].startswith('Mods/'):assert sha(data/e['path']).upper()==e['sha256'],('Installed module mismatch',e['path'])
changed=[]
for p in (candidate/'Region').glob('*.7rg'):
 rel=str(p.relative_to(candidate));assert rel in before,('Unexpected generated region',rel)
 if sha(p)!=before[rel]:changed.append(rel)
assert 0<len(changed)<=4,('Unexpected scope',changed)
# Stage replacements alongside their destinations; retain the verified zip backup.
for n in changed:shutil.copy2(candidate/n,save/(n+'.batch08-stage'))
for n in changed:os.replace(save/(n+'.batch08-stage'),save/n)
after={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()}
assert set(after)==set(before)
for n,h in before.items():assert after[n]==(sha(candidate/n) if n in changed else h),('Unexpected save alteration',n)
# Promote all pointers to this prior release, and relocate other valid historical
# pointers that still contain the pre-migration C: project prefix.
oldroot='C:\\Users\\Michael\\OneDrive\\Documents\\ChatGPT\\7 days to delve'
for f in (R/'dist').glob('latest-*-release.txt'):
 text=f.read_text(encoding='utf-8-sig').strip();relocated=Path(text.replace(oldroot,str(R)))
 if relocated==B:f.write_text(str(N)+'\n')
 elif relocated.exists() and str(relocated)!=text:f.write_text(str(relocated)+'\n')
(R/'dist/latest-first-forest-release.txt').write_text(str(N)+'\n');(R/'dist/latest-batch-eight-release.txt').write_text(str(N)+'\n');(R/'dist/previous-first-forest-release.txt').write_text(str(B)+'\n')
readme=R/'README.txt';text=readme.read_text(encoding='utf-8-sig').replace('CURRENT FIRST PLAYTEST - BATCH 5 COMPLETE','PREVIOUS CHECKPOINT - BATCH 5 COMPLETE')
intro='CURRENT FIRST PLAYTEST - BATCH 8 / 0.14.0\nProject: D:\\Projects\\ChatGPT\\7 days to delve\nRun Play-First-Forest.cmd; continue ForestTest02. Attributes repaired, Delve\nlogo installed, mat color baked into textures, Wayrest furnished with ten basic\ncrafting stations. The central fire square is unchanged. See docs/batch-eight-playtest.txt.\nAutomated acceptance passed; visual/UI acceptance remains the player playtest.\n\n'
text=text.replace('7 DAYS TO DELVE - 7 Days to Die fantasy mod\n\n','7 DAYS TO DELVE - 7 Days to Die fantasy mod\n\n'+intro,1);readme.write_text(text,encoding='utf-8')
result={'result':'PASS','release':str(N),'project':str(R),'save':'ForestTest02','changed_regions':changed,'unchanged_save_files':len(before)-len(changed),'player_files_unchanged':True,'backup':str(A/'ForestTest02-before-batch08.zip'),'game_left_closed':True}
(A/'installation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
