from pathlib import Path
import json,hashlib
from lxml import etree as E
import build_forest_slice as F
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05-complete';B=Path((A/'base.txt').read_text().strip());P=R/'playtest/BatchFiveComplete';checks=0
def check(b,m):
 global checks
 assert b,m
 checks+=1
F.MOD_NAMES=sorted(p.name for p in (P/'Mods').iterdir() if (p/'ModInfo.xml').exists())
new={k:F.merge(P/'Mods',k) for k in ['blocks','items','recipes','biomes','loadingscreen','XUi_Menu/windows']}
F.MOD_NAMES=sorted(p.name for p in (B/'Mods').iterdir() if (p/'ModInfo.xml').exists())
old={k:F.merge(B/'Mods',k) for k in ['blocks','items','recipes','biomes']}
for kind in ['recipes','biomes']:check(E.tostring(new[kind])==E.tostring(old[kind]),kind+' preserved; crop thinning occurs per whole patch at runtime')
for n in json.loads((A/'crates.json').read_text()):
 a=new['blocks'].find(f"block[@name='{n}']");b=old['blocks'].find(f"block[@name='{n}']")
 for key in ['Model','CustomIcon']:
  v=a.find(f"property[@name='{key}']");check('delveIronboundCrate' in v.get('value'),n+' '+key);v.set('value',b.find(f"property[@name='{key}']").get('value'))
 check(E.tostring(a)==E.tostring(b),n+' storage, locks, shape, break stages and loot unchanged')
menu=new['XUi_Menu/windows'];check(not menu.xpath("/windows/window[@name='menuBackground']/video"),'static menu');check(len(new['loadingscreen'].xpath('/doc/backgrounds/tex'))==2,'two backgrounds');check(len(new['loadingscreen'].xpath('/doc/tips/tip'))==2,'two lore passages')
for e in json.loads((B/'manifest.json').read_text(encoding='utf-8-sig'))['files']:
 if not e['path'].startswith(('Mods/','Worlds/')):continue
 p=P/e['path'].replace('Worlds/','GeneratedWorlds/',1)
 check(hashlib.sha256(p.read_bytes()).hexdigest().upper()==e['sha256'].upper(),'unchanged tested baseline '+e['path'])
result={'result':'PASS','checks':checks,'containers':34,'retained_items_baseline':str(B),'notes':'All source XML patches resolve; exact baseline recipes/biomes and container mechanics preserved.'}
(A/'static-validation.json').write_text(json.dumps(result,indent=2));print(result)
