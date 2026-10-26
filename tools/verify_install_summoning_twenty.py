from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1];A=R/'artifacts/summoning-20';N=Path((A/'release.txt').read_text().strip());m=json.loads((N/'manifest.json').read_text());data=Path((N/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
after={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()}
assert json.loads((A/'save-before.json').read_text())==after,'Live save changed'
mods=0
for e in m['files']:
 if e['path'].startswith('Mods/'):
  assert sha(data/e['path']).upper()==e['sha256'],e['path'];mods+=1
assert not (data/'Mods/StationProbe').exists(),'Test probe installed'
shutil.copy2(A/'Delve.dll',R/'src/Delve/Delve.dll')
(R/'dist/active-playtest-release.json').write_text(json.dumps(dict(release=str(N),version=m['version']),indent=2))
for name in ['latest-first-forest-release.txt','latest-summoning-release.txt']:(R/'dist'/name).write_text(str(N))
result=dict(result='PASS',release=str(N),saveFilesUnchanged=len(after),installedModFilesVerified=mods,backup=str(A/'ForestTest02-before.zip'))
(A/'installation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
