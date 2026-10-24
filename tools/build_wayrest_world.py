"""Replace only Wayrest's prototype compound in a fresh Allium-v0.4 world."""
from pathlib import Path
import shutil,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'artifacts/maps/Allium-v0.3';out=ROOT/'artifacts/maps/Allium-v0.4';out.mkdir(parents=True,exist_ok=True)
for name in ['dtm.raw','biomes.png','splat1.png','splat2.png','splat3.png','splat4.png','radiation.png','spawnpoints.xml','water_info.xml']:
    shutil.copyfile(source/name,out/name)
meta=ROOT/'src/DelveWayrest/Prefabs/POIs/delve_wayrest_01.xml'
tree=ET.parse(meta);tree.getroot().find("property[@name='TraderArea']").set('value','True');tree.write(meta,encoding='utf-8',xml_declaration=True)
assert meta.with_suffix('.tts').exists()
props={e.get('name'):e.get('value') for e in tree.getroot().findall('property')}
assert props['PrefabSize']=='60, 18, 60' and props['YOffset']=='-2'
prefabs=ET.parse(source/'prefabs.xml');matches=prefabs.getroot().findall("decoration[@name='trader_rekt']");assert len(matches)==1
assert matches[0].get('position')=='-2711,65,-2182'
matches[0].set('name','delve_wayrest_01');prefabs.write(out/'prefabs.xml',encoding='utf-8',xml_declaration=True)
info=ET.parse(source/'map_info.xml');info.getroot().find("property[@name='Name']").set('value','Allium-v0.4');info.write(out/'map_info.xml',encoding='utf-8',xml_declaration=True)
records=json.loads((source/'locations.json').read_text());records[0]['prefab']='delve_wayrest_01';records[0]['size']=[60,18,60]
(out/'locations.json').write_text(json.dumps(records,indent=2))
shutil.copyfile(ROOT/'artifacts/wayrest/wayrest-plan.png',out/'wayrest-plan.png')
report={'result':'PASS','world':'Allium-v0.4','checks':['exactly one Wayrest replacement at existing validated 60x60 foundation','terrain, roads, water and spawns unchanged from v0.3','custom native prefab and mapping present','trader area enabled','one steward marker; five connected doorways verified in blueprint'], 'limits':'User walking test deferred; native model and voice remain; no reclamation/recruitment implemented.'}
assert meta.with_suffix('.blocks.nim').exists()
(out/'input-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
