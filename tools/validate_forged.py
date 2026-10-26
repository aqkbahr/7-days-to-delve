"""M3 generated content coverage and runtime fixture inputs."""
import json
from lxml import etree as E
from build_forest_catalogue import ROOT,merged
d=json.loads((ROOT/'src/Forest/forged.json').read_text())
items=merged('items');recipes=merged('recipes');buffs=merged('buffs')
assert len(d['equipment'])==26 and len(d['runes'])==5
assert {r['role'] for r in d['equipment']}=={'Blades','Blunt','Polearms','Unarmed','Archery','Wands','Staffs','Totems','LightArmor','MediumArmor','HeavyArmor','Gathering'}
probe=E.Element('forged');checks=2
for r in d['recipes']:
    found=recipes.xpath('/recipes/recipe[@name=$n]',n=r['name']);assert len(found)==1
    rxml=found[0]
    assert rxml.get('craft_area')==r['station'] and int(rxml.get('count'))==r['count']
    assert {i.get('name'):int(i.get('count')) for i in rxml.findall('ingredient')}==r['ingredients']
    assert 'learnable' not in rxml.get('tags','') and r['rank']==20
    E.SubElement(probe,'recipe',name=r['name'],skill=r['skill'],station=r['station'],count=str(r['count']));checks+=4
for r in d['equipment']:
    it=items.xpath('/items/item[@name=$n]',n=r['name'])[0]
    assert it.find("property[@name='RepairTools']").get('value')==r['repair']
    assert it.find("property[@name='Extends']") is None,'Native stats must be explicitly resolved'
    assert it.findall(".//passive_effect[@name='DegradationMax']")[-1].get('value')=='400'
    E.SubElement(probe,'equipment',**{k:str(v) for k,v in r.items()});checks+=3
for r in d['runes']:
    it=items.xpath('/items/item[@name=$n]',n=r['name'])[0]
    assert it.find(".//passive_effect[@name='EntityDamage']").get('value')==str(r['damage'])
    assert it.find(".//passive_effect[@name='BlockDamage']").get('value')=='0'
    E.SubElement(probe,'rune',name=r['name'],damage=str(r['damage']));checks+=2
for name,duration in [('delveForgedHex','6'),('delveProtectiveWard','30')]:
    b=buffs.xpath('/buffs/buff[@name=$n]',n=name)[0]
    assert b.find('stack_type').get('value')=='replace' and b.find('duration').get('value')==duration;checks+=1
for amount in range(1,61):
    b=buffs.xpath('/buffs/buff[@name=$n]',n='delveHealPulse'+str(amount))[0]
    assert b.find(".//triggered_effect[@action='ModifyStats']").get('value')==str(amount);checks+=1
E.ElementTree(probe).write(str(ROOT/'artifacts/validation/forged-checks.xml'),pretty_print=True)
report=dict(result='PASS',checks=checks,equipment=26,runes=5,recipes=len(d['recipes']),scope='Generated definitions; engine and client acceptance are separate')
(ROOT/'artifacts/validation/forged-static.json').write_text(json.dumps(report,indent=2))
print(report)
