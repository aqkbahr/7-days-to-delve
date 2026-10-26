"""Final overlay for Batch 02. Keep firearm base classes for spell inheritance."""
from pathlib import Path
from lxml import etree as E
import json
import build_forest_slice as merge
ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'src/ZZZZDelveBatch02'
(MOD/'Config').mkdir(parents=True,exist_ok=True)
(MOD/'ModInfo.xml').write_text('<xml><Name value="ZZZZDelveBatch02"/><DisplayName value="Delve Batch 02"/><Version value="0.10.2"/><Author value="Delve"/></xml>\n')
merge.MOD_NAMES=['Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest','ZDelveRecruits','ZDelvePresentation','ZZZDelveBatch01']
items=merge.merge(ROOT/'src','items')
def prohibited(n):
    n=n or ''
    return n.startswith(('gunHandgun','gunShotgun','gunRifle','gunMG','gunExplosives','ammo9mm','ammo44','ammo762','ammoShotgun','ammoRocket','ammoJunkTurret','ammoBundle9mm','ammoBundle44','ammoBundle762','ammoBundleShotgun','ammoBundleJunkTurret')) or n=='gunBotT2JunkTurret'
banned={x.get('name') for x in items.getroot() if prohibited(x.get('name',''))}
def substitute(n):
    if n.endswith('Parts'):return 'resourceScrapIron'
    if n.startswith('ammo'):return 'ammoArrowStone'
    return 'delveBorderBow' if any(s in n for s in ['Rifle','MG','Shotgun','Turret','Explosives']) else 'delveBoneDagger'
reports={}
def save(kind,root):
    (MOD/'Config'/f'{kind}.xml').write_bytes(E.tostring(root,pretty_print=True,encoding='utf-8',xml_declaration=True))
for kind in ('recipes','loot','traders','quests','challenges','blocks'):
    doc=merge.merge(ROOT/'src',kind);patch=E.Element('configs');count=0
    for node in list(doc.iter()):
        if not isinstance(node.tag,str):continue
        attr='name' if node.tag in ('item','recipe','drop') else 'id' if node.tag=='reward' and node.get('type','').lower()=='item' else None
        if attr is None or node.get(attr) not in banned:continue
        path=doc.getpath(node)
        if kind=='recipes':E.SubElement(patch,'remove',xpath=path)
        else:E.SubElement(patch,'set',xpath=path+'/@'+attr).text=substitute(node.get(attr))
        count+=1
    # Numeric XPath recipe removals must run in reverse order to keep indices stable.
    if kind=='recipes':patch[:]=list(reversed(list(patch)))
    save(kind,patch);reports[kind]=count
patch=E.Element('configs')
for name in sorted(banned):
    path=f'/items/item[@name="{name}"]'
    local=items.xpath(path)[0]
    if local.find('property[@name="CreativeMode"]') is not None:E.SubElement(patch,'set',xpath=path+'/property[@name="CreativeMode"]/@value').text='None'
    else:E.SubElement(E.SubElement(patch,'append',xpath=path),'property',name='CreativeMode',value='None')
# Mixed starter/reward bundles must not retain firearm grants.
for node in items.xpath('//property[@name="Create_item"]'):
    names=node.get('value','').split(',')
    if not any(n in banned for n in names):continue
    E.SubElement(patch,'set',xpath=items.getpath(node)+'/@value').text=','.join(dict.fromkeys(substitute(n) if n in banned else n for n in names))
save('items',patch)
(ROOT/'artifacts/batch-02/firearm-removal.json').write_text(json.dumps(dict(banned=sorted(banned),rewritten=reports),indent=2)+'\n')
print('STAGED firearm exclusion:',len(banned),'items;',reports)
