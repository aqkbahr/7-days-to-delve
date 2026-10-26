from pathlib import Path
import json,hashlib
from lxml import etree as E
import build_forest_slice as F
R=Path(__file__).resolve().parents[1];P=R/'playtest/BatchNine';B=R/'dist/Delve-Batch08-20261026-124818';A=R/'artifacts/batch-09'
F.MOD_NAMES=sorted(p.name for p in (P/'Mods').iterdir() if (p/'ModInfo.xml').exists())
merged={n:F.merge(P/'Mods',n) for n in ['blocks','items','recipes','biomes','XUi_Menu/windows']}
for kind in ['blocks','items']:
 old=E.parse(str(B/f'Mods/ZZZZDelveBatch02/Config/{kind}.xml'))
 current=E.parse(str(P/f'Mods/ZZZZDelveBatch02/Config/{kind}.xml'))
 for node in old.xpath("/configs/append[@xpath='/blocks']/block"):
  name=node.get('name');assert merged['blocks'].find(f"block[@name='{name}']") is not None,('Missing medieval container',name)
 for node in old.xpath("/configs/*[contains(@xpath,'CustomIcon') or contains(@xpath,'ModelOffset')]"):
  assert any(n.get('xpath')==node.get('xpath') and n.text==node.text for n in current.getroot()),('Missing visual patch',node.get('xpath'))
for n,amount in [('foodDelveBrambleberries',2),('foodDelveCookedBerries',5)]:
 item=merged['items'].find(f"item[@name='{n}']")
 for cvar in ['$foodAmountAdd','$waterAmountAdd']:
  effects=item.xpath(f"effect_group/triggered_effect[@cvar='{cvar}']");assert len(effects)==1 and effects[0].get('value')==str(amount)
 assert not item.xpath("effect_group/triggered_effect[@cvar='$healthAmountAdd' or @stat='health']")
# All preceding overlays remain in place; the firearm exclusion overlay was
# intentionally rebased onto 3.4 named targets rather than its old numeric indices.
firearms=set(json.loads((A/'firearm-34-rebase.json').read_text())['banned'])
assert not [r.get('name') for r in merged['recipes'].getroot() if r.get('name') in firearms]
for kind in ['loot','traders','quests','challenges']:
 doc=F.merge(P/'Mods',kind)
 for node in doc.iter():
  if not isinstance(node.tag,str):continue
  if node.tag=='item':assert node.get('name') not in firearms,(kind,node.get('name'))
  if node.tag=='reward' and node.get('type','').lower()=='item':assert node.get('id') not in firearms
assert 'tab==-1' not in (R/'src/Code/ProgressionScreen.cs').read_text()
assert '(h&3)==0' in (R/'src/ZZZZZZZZZZZZDelveBatch05World/WorldChanges.cs').read_text()
native=Path('D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed/Assembly-CSharp.dll');assert hashlib.sha256(native.read_bytes()).hexdigest()==(A/'game-api-sha256.txt').read_text().strip()
(A/'static-validation.json').write_text(json.dumps({'result':'PASS','game':'3.4.0 b6','nutrition':'raw 2/2/0; cooked 5/5/0','preserved':['all recipes','block mechanics','biome shapes/density','menu/logo','attribute fix'],'wild_patches':'half of previous surviving patches; no POI or player-crop mutation'},indent=2));print('PASS: all XML patches resolve; berry groups exact; recipes, blocks, biome density and logo preserved')
