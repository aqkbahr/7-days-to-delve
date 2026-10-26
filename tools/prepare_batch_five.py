from pathlib import Path
import os,shutil,json,uuid
from lxml import etree as E
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05';B=Path((A/'base.txt').read_text(encoding='utf-8-sig').strip());P=R/'playtest/BatchFive'
assert not P.exists(),'Do not overwrite an existing test profile'
P.mkdir();manifest=json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))
for entry in manifest['files']:
 rel=entry['path']
 if not rel.startswith(('Mods/','Worlds/')):continue
 target=P/rel.replace('Worlds/','GeneratedWorlds/',1);target.parent.mkdir(parents=True,exist_ok=True)
 try:os.link(B/rel,target)
 except OSError:shutil.copy2(B/rel,target)
mod=R/'src/ZZZZZZZZZZZDelveBatch05';shutil.copytree(mod,P/'Mods'/mod.name,ignore=shutil.ignore_patterns('*.cs'))
cfg=E.parse(str(R/'playtest/StationUpgrades/serverconfig.xml'))
settings={'GameName':'BatchFive','UserDataFolder':str(P),'ServerName':'Batch Five Isolated Verification','ServerPort':'29210','TelnetPort':'29219','TelnetPassword':uuid.uuid4().hex,'ServerIP':'127.0.0.1','ServerVisibility':'0'}
for n,v in settings.items():cfg.find(f"property[@name='{n}']").set('value',v)
cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True)
(P/'profile.json').write_text(json.dumps({'GamePath':'D:/Steam/steamapps/common/7 Days To Die','ProfilePath':str(P)}))
probe=P/'Mods/StationProbe';probe.mkdir();(probe/'ModInfo.xml').write_text('<xml><Name value="StationProbe"/><DisplayName value="Batch 5 verification"/><Version value="1.0"/><Author value="Delve"/></xml>')
shutil.copy2(A/'checks.xml',probe/'addon-checks.xml')
(probe/'slice-checks.xml').write_text('<slice><station name="delveFieldCraftingMat" family="delveFieldCraftingMat" tier="1"/></slice>')
source=(R/'tools/forest/StationProbe.cs').read_text();source=source.replace('doc.Load(args[0])','doc.Load(Path.Combine(ModManager.GetMod("StationProbe",true).Path,"addon-checks.xml"))');(A/'BatchFiveStationProbe.cs').write_text(source)
source=(R/'tools/forest/StationPersistenceProbe.cs').read_text().replace('ConsoleCmdStationPersistence','ConsoleCmdMatPersistence').replace('stationpersist','matpersist').replace('[StationPersistence]','[MatPersistence]');(A/'MatPersistenceProbe.cs').write_text(source)
print(P)
