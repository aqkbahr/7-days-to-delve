from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-10';N=Path((A/'release.txt').read_text().strip());m=json.loads((N/'manifest.json').read_text());data=Path((N/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((A/'save-before.json').read_text());after={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()};assert before==after,'Save changed during install'
for e in m['files']:
 if e['path'].startswith('Mods/'):assert sha(data/e['path']).upper()==e['sha256'],e['path']
assert not (data/'Mods/StationProbe').exists(),'Test probe must not be installed'
shutil.copy2(R/'playtest/BatchTen/Mods/Delve/Delve.dll',R/'src/Delve/Delve.dll')
selection=dict(release=str(N),version=m['version']);(R/'dist/active-playtest-release.json').write_text(json.dumps(selection,indent=2))
for n in ['latest-first-forest-release.txt','latest-batch-ten-release.txt']:(R/'dist'/n).write_text(str(N))
(A/'installation.json').write_text(json.dumps(dict(result='PASS',release=str(N),saveFilesUnchanged=len(after),installedModsVerified=True,backup=str(A/'ForestTest02-before-batch10.zip')),indent=2));print('PASS installed mod hashes; '+str(len(after))+' save files unchanged; active launcher promoted.')
