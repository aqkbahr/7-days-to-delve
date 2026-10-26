"""Replace 3.3's positional firearm-removal selectors with named 3.4 selectors."""
from pathlib import Path
import json,shutil,re,copy
from lxml import etree as E
import build_forest_slice as F
R=Path(__file__).resolve().parents[1];P=R/'playtest/BatchNine';A=R/'artifacts/batch-09';M=P/'Mods/ZZZZDelveBatch02'
F.MOD_NAMES=sorted(p.name for p in (P/'Mods').iterdir() if (p/'ModInfo.xml').exists() and p.name<'ZZZZDelveBatch02')
def prohibited(n):return n.startswith(('gunHandgun','gunShotgun','gunRifle','gunMG','gunExplosives','ammo9mm','ammo44','ammo762','ammoShotgun','ammoRocket','ammoJunkTurret','ammoBundle9mm','ammoBundle44','ammoBundle762','ammoBundleShotgun','ammoBundleJunkTurret')) or n=='gunBotT2JunkTurret'
items=F.merge(P/'Mods','items');banned={x.get('name') for x in items.getroot() if isinstance(x.tag,str) and prohibited(x.get('name',''))}
def substitute(n):
 if n.endswith('Parts'):return 'resourceScrapIron'
 if n.startswith('ammo'):return 'ammoArrowStone'
 return 'delveBorderBow' if any(s in n for s in ['Rifle','MG','Shotgun','Turret','Explosives']) else 'delveBoneDagger'
def path(node):
 part=node.tag
 for attr in ['name','id','class']:
  if node.get(attr) is not None:
   assert "'" not in node.get(attr);part+=f"[@{attr}='{node.get(attr)}']";break
 else:
  parent=node.getparent()
  if parent is not None:
   peers=[n for n in parent if n.tag==node.tag]
   if len(peers)>1:part+=f'[{peers.index(node)+1}]'
 return (path(node.getparent()) if node.getparent() is not None else '')+'/'+part
reports={}
for kind in ['recipes','loot','traders','quests','challenges','blocks']:
 doc=F.merge(P/'Mods',kind);patch=E.Element('configs');seen=set()
 for node in doc.iter():
  if not isinstance(node.tag,str):continue
  attr='name' if node.tag in ('item','recipe','drop') else 'id' if node.tag=='reward' and node.get('type','').lower()=='item' else None
  if not attr or node.get(attr) not in banned:continue
  xp=path(node)
  if xp in seen:continue
  seen.add(xp)
  if kind=='recipes':E.SubElement(patch,'remove',xpath=xp)
  else:E.SubElement(patch,'set',xpath=xp+'/@'+attr).text=substitute(node.get(attr))
 (M/f'Config/{kind}.xml').write_bytes(E.tostring(patch,encoding='utf-8',pretty_print=True));reports[kind]=len(patch)
patch=E.Element('configs')
for name in sorted(banned):
 xp=f"/items/item[@name='{name}']";node=items.xpath(xp)[0]
 if node.find("property[@name='CreativeMode']") is not None:E.SubElement(patch,'set',xpath=xp+"/property[@name='CreativeMode']/@value").text='None'
 else:E.SubElement(E.SubElement(patch,'append',xpath=xp),'property',name='CreativeMode',value='None')
for node in items.xpath("//property[@name='Create_item']"):
 names=node.get('value','').split(',')
 if any(n in banned for n in names):E.SubElement(patch,'set',xpath=path(node)+'/@value').text=','.join(dict.fromkeys(substitute(n) if n in banned else n for n in names))
(M/'Config/items.xml').write_bytes(E.tostring(patch,encoding='utf-8',pretty_print=True));reports['items']=len(patch)
baseline=Path((A/'base.txt').read_text().strip())/'Mods/ZZZZDelveBatch02/Config'
# The same module also contains medieval containers, custom icons and offsets.
# Retain every named non-firearm change rather than replacing the whole module.
for kind in ['items','blocks']:
 patch=E.parse(str(M/f'Config/{kind}.xml')).getroot()
 for node in E.parse(str(baseline/f'{kind}.xml')).getroot():
  xp=node.get('xpath','')
  if re.search(r'\[\d+\]',xp):continue
  names=re.findall(r'@name=[\"\x27]([^\"\x27]+)',xp)
  if kind=='items' and names and names[0] in banned:continue
  patch.append(copy.deepcopy(node))
 (M/f'Config/{kind}.xml').write_bytes(E.tostring(patch,encoding='utf-8',pretty_print=True))
 reports[kind]=len(patch)
for n in list(reports):shutil.copy2(M/f'Config/{n}.xml',R/f'src/ZZZZDelveBatch02/Config/{n}.xml')
(A/'firearm-34-rebase.json').write_text(json.dumps({'banned':sorted(banned),'patch_counts':reports,'reason':'3.4 inserted native definitions; positional 3.3 selectors targeted wrong entries'},indent=2));print(reports)
