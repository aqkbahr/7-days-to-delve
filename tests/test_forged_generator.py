"""Contract test with M2 source and synthetic native stubs, not engine validation."""
from pathlib import Path
from xml.etree import ElementTree as E
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import forged_equipment as generator
fixture=ROOT/'artifacts/tests/forged-generator-fixture'
(fixture/'src/Forest').mkdir(parents=True,exist_ok=True)
(fixture/'src/Code').mkdir(parents=True,exist_ok=True)
generator.ROOT=fixture
items=E.parse(ROOT/'playtest/ForestM2/Mods/Delve/Config/items.xml').find("append[@xpath='/items']")
native=E.Element('items')
parents={p.get('value') for p in items.findall(".//property[@name='Extends']")}
parents|={'gunBowT1IronCrossbow','meleeToolPickT1IronPickaxe','meleeToolAxeT1IronFireaxe','meleeToolShovelT1IronShovel'}
for name in sorted(parents):
    stub=E.SubElement(native,'item',name=name)
    E.SubElement(stub,'property',name='Tags',value='fixture')
    eg=E.SubElement(stub,'effect_group');E.SubElement(eg,'passive_effect',name='EntityDamage',operation='base_set',value='10')
recipes=E.Element('configs');E.SubElement(recipes,'append',xpath='/recipes');buffs=E.Element('append')
def node(parent,tag,**attrs):return E.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
def prop(parent,key,value):return node(parent,'property',name=key,value=value)
def effect(parent,name,value,operation='base_add',**attrs):return node(parent,'passive_effect',name=name,value=value,operation=operation,**attrs)
texts={}
def loc(key,value):texts[key]=value;return key
generator.extend({'items':E.ElementTree(native)},items,recipes,buffs,node,prop,effect,loc)
d=json.loads((fixture/'src/Forest/forged.json').read_text());assert len(d['recipes'])==31
assert len(d['equipment'])==26 and len(d['runes'])==5
assert len({r['name'] for r in d['recipes']})==31
for r in d['recipes']:
    assert r['rank']==20 and r['ingredients'] and all(v>0 for v in r['ingredients'].values())
    assert items.find(f"item[@name='{r['name']}']") is not None
    assert r['name']+'Desc' in texts
for r in d['equipment']:
    it=items.find(f"item[@name='{r['name']}']")
    assert it.find("property[@name='Extends']") is None
    assert it.find("property[@name='RepairTools']").get('value')==r['repair']
    assert it.findall(".//passive_effect[@name='DegradationMax']")[-1].get('value')=='400'
for r in d['runes']:
    it=items.find(f"item[@name='{r['name']}']")
    assert it.find(".//passive_effect[@name='EntityDamage']").get('value')==str(r['damage'])
    assert it.find(".//passive_effect[@name='BlockDamage']").get('value')=='0'
assert len([b for b in buffs if b.get('name','').startswith('delveHealPulse')])==60
assert items.find("item[@name='delveForgedMendingTotem']/property[@class='Action0']/property[@name='Magazine_items']").get('value')=='delveEtchedHealingRune'
print('PASS: generator contract for 31 recipes, 26 equipment items, five payloads and 60 bounded heal pulses; synthetic native stubs, not engine validation')
