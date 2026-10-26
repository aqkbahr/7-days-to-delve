"""Package only manifest-listed content and promote after native acceptance."""
from pathlib import Path
from datetime import datetime
import hashlib,json,shutil,os
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'artifacts/station-upgrades';EVIDENCE=ROOT/'artifacts/validation/station-upgrades'
BASE=Path((ART/'base.txt').read_text(encoding='utf-8-sig').strip());MOD=ROOT/'src/ZZZZZZZZZZDelveStations'
selected=ROOT/'dist/latest-first-forest-release.txt'
assert Path(selected.read_text(encoding='utf-8-sig').strip())==BASE,'Selected build changed; reconcile first'
manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
for e in manifest['files']:assert sha(BASE/e['path'])==e['sha256'].upper(),e['path']
assert json.loads((ART/'static-validation.json').read_text())['result']=='PASS'
for filename,markers in {'native-final.txt':['[StationProbe] PASS','253 recipe variants','PASS: 617'], 'batch04-final.txt':['[Batch04] PASS'], 'persistence-seed-server.log':['[AddonPersistence] PASS seed 27'], 'persistence-check-server.log':['[AddonPersistence] PASS check 27']}.items():
    content=(EVIDENCE/filename).read_text(encoding='utf-8-sig')
    for marker in markers:assert marker in content,(filename,marker)
    assert '[StationProbe] FAIL' not in content and '[AddonPersistence] FAIL' not in content and '[Batch04] FAIL' not in content,filename
for p in MOD.rglob('*'):
    if p.is_file():assert sha(p)==sha(ROOT/'playtest/StationUpgrades/Mods'/MOD.name/p.relative_to(MOD)),p
for e in manifest['files']:
    if e['path'].startswith(('Mods/','Worlds/')):assert sha(ROOT/'playtest/StationUpgrades'/e['path'].replace('Worlds/','GeneratedWorlds/',1))==e['sha256'].upper(),('untested production file',e['path'])
release=ROOT/'dist'/('Delve-Station-Addons-'+datetime.now().strftime('%Y%m%d-%H%M%S'));release.mkdir()
for e in manifest['files']:
    src=BASE/e['path'];dst=release/e['path'];dst.parent.mkdir(parents=True,exist_ok=True)
    # Immutable production assets may share file data; metadata remains independent.
    if e['path'].startswith(('Mods/','Worlds/')):
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
    else:shutil.copy2(src,dst)
shutil.copytree(MOD,release/'Mods'/MOD.name)
shutil.copy2(ART/'catalogue.json',release/'Catalogue/first-playtest.json')
shutil.copy2(ART/'STATION-UPGRADES.txt',release/'STATION-UPGRADES.txt')
shutil.copy2(ART/'STATION-UPGRADES.txt',release/'CRAFTING-STATIONS.txt')
notes='''STATION ADD-ONS - 0.12.0
One or two bases per crafting profession. Build bases at proficiency 1; install
removable add-ons at 10 and 20. These replace separate station tier construction.
Existing station blocks remain usable with the new add-on slots. See
STATION-UPGRADES.txt for stations, upgrade costs, recipe requirements and horde preparation.
Optional vendor tomes, Pitch, equipment routing, nearby storage and the terrain
correction remain included. The current save-data folder is preserved.
The add-on update works with existing saves. A new save is still necessary to
receive the earlier POI terrain correction if you have not already started one.
'''
(release/'START-HERE.txt').write_text(notes,encoding='utf-8')
validation='''STATION ADD-ONS - 0.12.0
PASS: 252 recipes through proficiency 20, plus the preserved Alchemy-40 charge.
PASS: all 20 proficiency stages resolve every exact recipe using Forest sources,
stations, add-ons and water production; no later-stage dependencies.
PASS: native recipe gates, ingredient checks, practice ownership, native station
menus, required-tool absence/wrong/installed/removal and native queue outputs.
PASS: 27 base/legacy station variants serialize 2/3 installed tools through disk
and both network modes. All 27 placed stations retain installed tools, stored
output and exact queued recipes across an actual shutdown/restart; reloaded jobs finish.
PASS: 617 core checks and Batch 04 storage/rune backend regression.
PASS: baseline production files preserved; tested modules match packaged modules.
Native UI behavior is exercised through the game controllers; human visual,
balance and remote-client multiplayer acceptance remain playtest checks.
See Evidence/StationAddons for exact counts and logs.

Historical validation follows (earlier station-tier design is superseded).

'''
(release/'VALIDATION.txt').write_text(validation+(BASE/'VALIDATION.txt').read_text(encoding='utf-8-sig'),encoding='utf-8')
dest=release/'Evidence/StationAddons';shutil.copytree(EVIDENCE,dest)
for n in ('base.txt','static-validation.json','design.json','checks.xml'):shutil.copy2(ART/n,dest/n)
for p in (ROOT/'src/StationUpgrades').glob('*.cs'):shutil.copy2(p,dest/p.name)
manifest.update(version='0.12.0-station-addons',name='Allium Station Add-ons')
manifest['files']=[dict(path=p.relative_to(release).as_posix(),sha256=sha(p)) for p in sorted(release.rglob('*')) if p.is_file() and p!=release/'manifest.json']
(release/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for e in manifest['files']:assert sha(release/e['path'])==e['sha256'],e['path']
assert Path(selected.read_text(encoding='utf-8-sig').strip())==BASE,'Selected build changed during packaging'
for pointer in (ROOT/'dist').glob('latest-*-release.txt'):
    if Path(pointer.read_text(encoding='utf-8-sig').strip())==BASE:pointer.write_text(str(release)+'\n',encoding='utf-8')
(ROOT/'dist/latest-station-addons-release.txt').write_text(str(release)+'\n',encoding='utf-8')
print('PASS packaged, verified and selected:',release)
