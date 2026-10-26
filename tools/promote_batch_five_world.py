from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05-complete';B=Path((A/'base.txt').read_text().strip());N=Path((A/'release.txt').read_text().strip());pointer=R/'dist/latest-first-forest-release.txt'
assert Path(pointer.read_text(encoding='utf-8-sig').strip())==B,'Selected baseline changed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
data=Path((N/'save-data-location.txt').read_text(encoding='utf-8-sig').strip());save=data/'Saves/Allium-v0.10/ForestTest02'
before=json.loads((A/'save-before.json').read_text());after={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()};assert before==after,'Save files changed'
manifest=json.loads((N/'manifest.json').read_text())
for e in manifest['files']:
 assert sha(N/e['path'])==e['sha256'],e['path']
 if e['path'].startswith('Mods/'):assert sha(data/e['path'])==e['sha256'],('Installed mismatch',e['path'])
assert {p.name for p in (data/'Mods').iterdir() if p.is_dir()}=={p.name for p in (N/'Mods').iterdir() if p.is_dir()},'Unexpected installed mod directory'
for p in (R/'dist').glob('latest-*-release.txt'):
 if Path(p.read_text(encoding='utf-8-sig').strip())==B:p.write_text(str(N)+'\n')
(R/'dist/previous-first-forest-release.txt').write_text(str(B)+'\n');pointer.write_text(str(N)+'\n')
(R/'dist/latest-batch-five-release.txt').write_text(str(N)+'\n')
(A/'installation.json').write_text(json.dumps({'result':'PASS','release':str(N),'data':str(data),'save':'ForestTest02','save_files_unchanged':len(before),'installed_files_verified':len([e for e in manifest['files'] if e['path'].startswith('Mods/')])},indent=2))
readme=R/'README.txt';text=readme.read_text(encoding='utf-8-sig');text=text.replace('CURRENT FIRST PLAYTEST - BATCH 5 / 0.13.0','PREVIOUS ITEMS CHECKPOINT - BATCH 5 / 0.13.0')
text=text.replace('7 DAYS TO DELVE - 7 Days to Die fantasy mod\n','7 DAYS TO DELVE - 7 Days to Die fantasy mod\n\nCURRENT FIRST PLAYTEST - BATCH 5 COMPLETE / 0.13.1\nRun Play-First-Forest.cmd and continue ForestTest02. Game data stays on D:.\nIncludes the Field Crafting Mat, starter/Forged rebalance, raw berries 3/3,\nroughly half as many wild crop patches, full 1m Supply Crates, medieval menu\nand two loading illustrations with lore. See docs/batch-five-complete.txt.\nForestTest02 was backed up and all save files verified unchanged on installation.\nAutomated backend acceptance passed. Hands-on UI/visual acceptance remains\nyour playtest; no graphics settings were changed.\n')
readme.write_text(text,encoding='utf-8');print((A/'installation.json').read_text())
