from pathlib import Path
import json,shutil,zipfile,hashlib,uuid
from lxml import etree as E
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-11';P=R/'playtest/BatchEleven';B=Path(json.loads((R/'dist/active-playtest-release.json').read_text())['release']);M=R/'src/ZZZZZZZZZZZZZZZZZDelveBatch11'
assert not P.exists();A.mkdir(exist_ok=True);(A/'base.txt').write_text(str(B))
save=Path((B/'save-data-location.txt').read_text().strip())/'Saves/Allium-v0.10/ForestTest02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(A/'save-before.json').write_text(json.dumps({str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()},indent=2))
with zipfile.ZipFile(A/'ForestTest02-before-batch11.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in save.rglob('*'):
  if p.is_file():z.write(p,'ForestTest02/'+p.relative_to(save).as_posix())
shutil.copytree(save,P/'Saves/Allium-v0.10/ForestTest02')
for e in json.loads((B/'manifest.json').read_text())['files']:
 n=e['path']
 if n.startswith(('Mods/','Worlds/')):
  dest=P/n.replace('Worlds/','GeneratedWorlds/',1);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/n,dest)
probe=P/'Mods/StationProbe';probe.mkdir()
for n in ['ModInfo.xml','StationProbe.dll','slice-checks.xml','addon-checks.xml','placed-stations.xml']:
 shutil.copy2(R/'playtest/BatchNine/Mods/StationProbe'/n,probe/n)
cfg=E.parse(str(R/'playtest/BatchNine/serverconfig.xml'))
for n,v in {'UserDataFolder':str(P),'ServerName':'Delve Current Playtest Batch Verification','ServerPort':'29710','TelnetPort':'29719','TelnetPassword':uuid.uuid4().hex}.items():cfg.find(f"property[@name='{n}']").set('value',v)
cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True);(P/'profile.json').write_text(json.dumps({'GamePath':'D:/Steam/steamapps/common/7 Days To Die','ProfilePath':str(P)}))
for n in ['Config','Resources','UIAtlases/ItemIconAtlas']:(M/n).mkdir(parents=True,exist_ok=True)
(M/'ModInfo.xml').write_text('<xml><Name value="DelveBatch11"/><DisplayName value="Delve - Magic, Harvesting and Station Tools"/><Version value="0.17.0"/><Author value="Delve"/></xml>')
print('Backed up ForestTest02 and prepared isolated BatchEleven candidate')
