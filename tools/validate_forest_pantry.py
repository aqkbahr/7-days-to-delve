"""Validate planting chains, seed access, recipe ownership and regional distribution."""
from pathlib import Path
from lxml import etree as E
import json, copy

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
data=json.loads((ROOT/'src/Forest/pantry.json').read_text())
merged={}
for kind in ('items','blocks','biomes','recipes'):
    doc=E.parse(str(BASE/(kind+'.xml')))
    for patch in E.parse(str(ROOT/'src/Delve/Config'/(kind+'.xml'))).getroot():
        targets=doc.xpath(patch.get('xpath'));assert targets,patch.get('xpath')
        for target in targets:
            if patch.tag=='append':
                for child in patch:target.append(copy.deepcopy(child))
            elif patch.tag=='set':target.getparent().set(target.attrname,patch.text or '')
            elif patch.tag=='remove':target.getparent().remove(target)
            else:raise AssertionError(patch.tag)
    merged[kind]=doc
blocks={b.get('name'):b for b in merged['blocks'].getroot()}
items={b.get('name'):b for b in merged['items'].getroot()}
checks=0
for p in data['plants']:
    stem=p['seed'][:-1]
    for a,b in [('1','2'),('2','3HarvestPlayer')]:
        block=blocks[stem+a]
        assert block.find("property[@class='PlantGrowing']/property[@name='Next']").get('value')==stem+b
        checks+=1
    for name in (p['wild'],p['cultivated']):
        block=blocks[name]
        assert block.find('dropextendsoff') is not None
        assert block.find(f"drop[@event='Harvest'][@name='{p['item']}']") is not None
        assert block.find(f"drop[@event='Destroy'][@name='{p['seed']}']") is not None
        checks+=3
    assert p['item'] in items
    assert blocks[p['cultivated']].find("drop[@event='Destroy']").get('prob')=='1'
    checks+=2
for biome,entries in data['biomes'].items():
    decorations=merged['biomes'].xpath(f"/worldgeneration/biomes/biome[@name='{biome}']//decorations")
    assert decorations
    for entry in entries:
        name=entry['block'];assert name in blocks
        for deco in decorations:
            matches=deco.findall(f"decoration[@blockname='{name}']")
            assert len(matches)==1,(biome,name,'duplicate or absent spawn')
            assert 0<float(matches[0].get('prob'))<1
            checks+=2
        seed=name.replace('3Harvest','1')
        assert len(blocks[name].findall(f"drop[@event='Destroy'][@name='{seed}']"))==1
        checks+=1
# Every native, conventionally named cultivated crop has a wild acquisition biome.
distributed={e['block'] for es in data['biomes'].values() for e in es}
for name in blocks:
    if name and name.startswith('planted') and name.endswith('3HarvestPlayer'):
        assert name[:-6] in distributed,('Missing farmable crop',name)
        checks+=1
for row in data['recipes']:
    found=merged['recipes'].xpath(f"/recipes/recipe[@name='{row['name']}']")
    assert len(found)==1,row['name']
    assert row['rank'] in (1,10,20)
    assert row['name'] in items or row['name'] in blocks
    for ingredient in found[0].findall('ingredient'):
        assert ingredient.get('name') in items or ingredient.get('name') in blocks
        assert int(ingredient.get('count'))>0
    checks+=4
checks_doc=E.Element('checks')
for row in data['recipes']:
    E.SubElement(checks_doc,'recipe',**{k:str(row[k]) for k in ('name','skill','rank','count')})
path=ROOT/'artifacts/validation/pantry-checks.xml';path.parent.mkdir(parents=True,exist_ok=True)
E.ElementTree(checks_doc).write(str(path),pretty_print=True)
print(f'PASS: {checks} pantry checks; {len(data["recipes"])} recipes; {len(distributed)} farmable crop types with wild acquisition.')


