from pathlib import Path
import json
from lxml import etree as E
import build_forest_slice as merger
ROOT=Path(__file__).resolve().parents[1]
merger.MOD_NAMES=['Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest','ZDelveRecruits','ZDelvePresentation','ZZZDelveBatch01','ZZZZDelveBatch02']
source=ROOT/'artifacts/batch-02/candidate/Mods'
banned=set(json.loads((ROOT/'artifacts/batch-02/firearm-removal.json').read_text())['banned'])
checks=[]
for kind in ('recipes','loot','traders','quests','items'):
    tree=merger.merge(source,kind)
    if kind=='items':
        for item in tree.xpath('/items/item'):
            if item.get('name') in banned:assert item.find('property[@name="CreativeMode"]').get('value')=='None'
        for node in tree.xpath('//property[@name="Create_item"]'):assert not banned.intersection(node.get('value','').split(',')),E.tostring(node)
    else:
        for node in tree.iter():
            attr='name' if node.tag in ('item','recipe','drop') else 'id' if node.tag=='reward' and node.get('type','').lower()=='item' else None
            if attr:assert node.get(attr) not in banned,(kind,E.tostring(node))
    if kind=='recipes':
        for name in ('meleeWpnClubT0WoodenClub','gunBowT0PrimitiveBow','meleeWpnBladeT0BoneKnife'):
            recipes=tree.xpath(f'/recipes/recipe[@name="{name}"]');assert len(recipes)==1,(name,len(recipes))
            recipe=recipes[0];assert not recipe.get('craft_area') and not recipe.get('tags'),E.tostring(recipe)
    checks.append(kind+' firearm/access closure PASS')
(ROOT/'artifacts/batch-02/content-validation.txt').write_text('\n'.join(checks)+'\n')
print('\n'.join(checks))
