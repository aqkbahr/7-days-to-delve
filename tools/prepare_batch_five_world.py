from pathlib import Path
import shutil,os,json,uuid
from lxml import etree as E
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05-complete';B=Path((A/'base.txt').read_text().strip());P=R/'playtest/BatchFiveComplete';M=R/'src/ZZZZZZZZZZZZDelveBatch05World'
assert not P.exists(),'Do not overwrite test profile'
P.mkdir()
for e in json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))['files']:
 rel=e['path']
 if not rel.startswith(('Mods/','Worlds/')):continue
 target=P/rel.replace('Worlds/','GeneratedWorlds/',1);target.parent.mkdir(parents=True,exist_ok=True);os.link(B/rel,target)
shutil.copytree(M,P/'Mods'/M.name,ignore=shutil.ignore_patterns('*.cs'))
shutil.copytree(R/'playtest/BatchFive/Mods/StationProbe',P/'Mods/StationProbe')
cfg=E.parse(str(R/'playtest/BatchFive/serverconfig.xml'))
for n,v in {'GameName':'BatchFiveComplete','UserDataFolder':str(P),'ServerName':'Batch Five Complete Verification','ServerPort':'29310','TelnetPort':'29319','TelnetPassword':uuid.uuid4().hex}.items():cfg.find(f"property[@name='{n}']").set('value',v)
cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True)
(P/'profile.json').write_text(json.dumps({'GamePath':'D:/Steam/steamapps/common/7 Days To Die','ProfilePath':str(P)}))
print(P)
