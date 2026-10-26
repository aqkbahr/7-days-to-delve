from pathlib import Path
from copy import deepcopy
from lxml import etree as E
import json,csv
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
pin=ROOT/'artifacts/forest-current-build-base.txt'
if not pin.exists():pin=ROOT/'artifacts/forest-base-release.txt'
release=Path((pin if pin.exists() else ROOT/'dist/latest-allium-release.txt').read_text(encoding='utf-8-sig').strip())
mod=ROOT/'src/ZDelveForest'; errors=[]; operations=0; merged={}; before_module={}
for patch in (mod/'Config').glob('*.xml'):
    doc=E.parse(str(BASE/patch.name))
    for folder in [p for p in sorted((release/'Mods').iterdir()) if p.is_dir() and p.name!='ZDelveForest']+[mod]:
        if folder==mod:before_module[patch.stem]=deepcopy(doc)
        file=folder/'Config'/patch.name
        if not file.exists():continue
        for op in E.parse(str(file)).getroot():
            targets=doc.xpath(op.get('xpath'))
            if not targets:errors.append(f'{file}: unmatched {op.get("xpath")}')
            for target in targets:
                if op.tag=='append':
                    for child in op:target.append(deepcopy(child))
                elif op.tag=='set':
                    if getattr(target,'is_attribute',False):target.getparent().set(target.attrname,op.text or '')
                    else:target.text=op.text or ''
                elif op.tag=='remove':target.getparent().remove(target)
                else:errors.append('Unsupported patch '+op.tag)
            if folder==mod:operations+=1
    merged[patch.stem]=doc
roster=json.loads((ROOT/'src/Forest/roster.json').read_text())
entities={n.get('name'):n for n in merged['entityclasses'].xpath('/entity_classes/entity_class')}
items={n.get('name'):n for n in merged['items'].xpath('/items/item')}
groups={n.get('name'):n for n in merged['entitygroups'].xpath('/entitygroups/entitygroup')}
colors={n.get('name') for n in merged['entityclasses'].xpath('/entity_classes/color')}
for e in roster:
    definition=entities[e['id']]
    assert definition.get('extends')==e['parent'] and e['parent'] in entities
    if e['parent'].startswith('animal'):assert definition.find("property[@name='DelveTint']").get('value')==e['color']
    else:assert definition.find("property[@name='MatColor']").get('value') in colors
    assert definition.find("property[@name='HandItem']").get('value') in items
    assert float(definition.find("effect_group/passive_effect[@name='HealthMax']").get('value'))==e['hp']
    for drop in definition.findall('drop'):assert drop.get('name') in items
for group in groups.values():
    if group.get('name').startswith(('delveForest_','delveArbor')):
        for e in group:assert e.get('n') in entities or e.get('n')=='none'
        assert abs(sum(float(n.get('p','1')) for n in group)-1)<.00001
for recipe in E.parse(str(mod/'Config/recipes.xml')).xpath('//recipe'):
    assert recipe.get('name') in items
    for ingredient in recipe:assert ingredient.get('name') in items
# Every original biome slot retains its population, timing, density and tag rules.
vanilla=before_module['spawning']
actual=merged['spawning']
for biome in vanilla.xpath('/spawning/biome'):
    for spawn in biome:
        if not isinstance(spawn.tag,str):continue
        match=actual.xpath('/spawning/biome[@name=$b]/spawn[@id=$s]',b=biome.get('name'),s=spawn.get('id'))
        assert len(match)==1
        assert {k:v for k,v in match[0].attrib.items() if k!='entitygroup'}=={k:v for k,v in spawn.attrib.items() if k!='entitygroup'}
        assert match[0].get('entitygroup') in groups
policies=E.parse(str(mod/'ForestEncounters.xml')).getroot()
assert len(policies)>=15
for p in policies:
    original=E.parse(str(release/'Mods/DelveWayrest/Prefabs/POIs'/(p.get('name')+'.xml')))
    value=original.xpath("/prefab/property[@name='SleeperVolumeGroup']/@value")[0].replace('\n','').split(',')
    index=int(p.get('volume'));assert int(value[index*3+2])>=2
    assert p.get('kind') in ['corrupted','imp','soldier','occupation']
    assert p.get('name').startswith('delve_forest_')
valid=set(json.loads((ROOT/'artifacts/inspection/passive-effects.json').read_text(encoding='utf-8-sig')))
for path in (mod/'Config').glob('*.xml'):
    for fx in E.parse(str(path)).xpath('//passive_effect'):assert fx.get('name') in valid
result={'result':'FAIL' if errors else 'PASS','patch_operations':operations,'roster':len(roster),'poi_assignments':len(policies),'errors':errors,'scope':'Merged XML, native references, population invariants and assignment bounds; not combat or rendered art.'}
out=ROOT/'artifacts/validation/forest';out.mkdir(parents=True,exist_ok=True)
(out/'content.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
