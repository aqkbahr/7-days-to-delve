import json
from pathlib import Path
from lxml import etree as E
from build_forest_catalogue import merged,ROOT
d=json.loads((ROOT/'src/Forest/processing.json').read_text())
items=merged('items');blocks=merged('blocks');recipes=merged('recipes');buffs=merged('buffs')
probe=E.Element('processing'); checks=0
for r in d['recipes']:
    candidates=recipes.xpath('/recipes/recipe[@name=$n]',n=r['name'])
    assert any({i.get('name'):int(i.get('count')) for i in c.findall('ingredient')}==r['ingredients'] and c.get('craft_area','')==r['station'] and int(c.get('count','1'))==r['count'] and 'learnable' not in c.get('tags','') for c in candidates),r
    entry=E.SubElement(probe,'recipe',name=r['name'],skill=r['skill'] or '',rank=str(r['rank']),count=str(r['count']),station=r['station'])
    for k,v in r['ingredients'].items():E.SubElement(entry,'ingredient',name=k,count=str(v))
    checks+=1
for s in d['stations']:
    b=blocks.xpath('/blocks/block[@name=$n]',n=s['name'])[0]
    assert b.find("property[@class='Workstation']/property[@name='Modules']").get('value')=='output'
    assert b.find('dropextendsoff') is not None
    E.SubElement(probe,'station',name=s['name']);checks+=2
for name,supply in d['repairs'].items():
    it=items.xpath('/items/item[@name=$n]',n=name)[0]
    assert it.find("property[@name='RepairTools']").get('value')==supply
    kit=items.xpath('/items/item[@name=$n]',n=supply)[0]
    assert kit.find("property[@name='RepairAmount']").get('value')=='32000'
    E.SubElement(probe,'repair',name=name,supply=supply);checks+=2
for category in ['meal','drink']:
    for name in d[category+'_items']:
        it=items.xpath('/items/item[@name=$n]',n=name)[0]
        assert not it.xpath('.//triggered_effect[@cvar=".foodStaminaBonusAdd"]')
        assert it.xpath('.//triggered_effect[@buff=$b]',b='delveForest'+category.title())
        checks+=2
for name in ['delveForestMeal','delveForestDrink']:
    b=buffs.xpath('/buffs/buff[@name=$n]',n=name)[0]
    assert b.find('stack_type').get('value')=='replace' and b.find('duration').get('value')=='900';checks+=1
E.ElementTree(probe).write(str(ROOT/'artifacts/validation/processing-checks.xml'),pretty_print=True)
report=dict(result='PASS',checks=checks,recipes=len(d['recipes']),stations=len(d['stations']),repair_bindings=len(d['repairs']))
(ROOT/'artifacts/validation/processing-static.json').write_text(json.dumps(report,indent=2))
print(report)
