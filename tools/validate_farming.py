"""Check the merged farming economy, station isolation and consuming contracts."""
from pathlib import Path
from lxml import etree as E
import copy,json,argparse

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
data=json.loads((ROOT/'src/Farming/first-pass.json').read_text())
parser=argparse.ArgumentParser()
parser.add_argument('--mods',type=Path)
args=parser.parse_args()
mods=sorted(args.mods.iterdir()) if args.mods else [ROOT/'src/Delve']
merged={}
for name in ['blocks','recipes','items','quests','XUi_InGame/xui']:
    doc=E.parse(str(BASE/(name+'.xml')))
    operations=[]
    for mod in mods:
        path=mod/'Config'/(name+'.xml')
        if path.exists():operations.extend(E.parse(str(path)).getroot())
    for op in operations:
        targets=doc.xpath(op.get('xpath'));assert targets,op.get('xpath')
        for target in targets:
            if op.tag=='append':
                for child in op:target.append(copy.deepcopy(child))
            elif op.tag=='set':target.getparent().set(target.attrname,op.text or '')
            elif op.tag=='remove':target.getparent().remove(target)
            else:raise AssertionError(op.tag)
    merged[name]=doc

def one(kind,xpath):
    matches=merged[kind].xpath(xpath);assert len(matches)==1,(kind,xpath,len(matches))
    return matches[0]

checks=0
for row in data['seeds']:
    drop=one('blocks',f"/blocks/block[@name='{row['ripe']}']/drop[@event='Destroy'][@name='{row['seed']}']")
    assert drop.get('prob')=='1' and drop.get('count')=='1'
    # No specialization or optional bonus is needed for a positive harvest.
    harvest=one('blocks',f"/blocks/block[@name='{row['ripe']}']/drop[@event='Harvest'][@tag='cropHarvest']")
    assert int(harvest.get('count'))>=2
    recipe=one('recipes',f"/recipes/recipe[@name='{row['seed']}']")
    assert 'learnable' not in recipe.get('tags','')
    assert int(recipe.find('ingredient').get('count'))==2
    checks+=4
for row in data['stations']:
    name=row['name'];block=one('blocks',f"/blocks/block[@name='{name}']")
    assert block.find("property[@name='Extends']").get('value')=='workbench'
    assert block.find("property[@class='Workstation']/property[@name='CraftingAreaRecipes']").get('value')==name
    assert block.find('dropextendsoff') is not None
    assert block.find("drop[@event='Destroy']").get('count')=='0'
    one('XUi_InGame/xui',f"/xui/window_group[@name='workstation_{name}']")
    checks+=5
for row in data['recipes']:
    r=one('recipes',f"/recipes/recipe[@name='{row['name']}']")
    assert r.get('craft_area','')==row['station']
    assert int(r.get('count'))==row['count']
    assert {i.get('name'):int(i.get('count')) for i in r.findall('ingredient')}==row['ingredients']
    assert all(v>0 for v in row['ingredients'].values())
    assert row['name'] not in row['ingredients']
    assert row['level'] in (1,6,11,16,20)
    checks+=6
for row in data['orders']:
    q=one('quests',f"/quests/quest[@id='{row['quest']}']")
    assert q.find("property[@name='repeatable']").get('value')=='true'
    assert q.find("property[@name='shareable']").get('value')=='false'
    assert len(q.findall('objective'))==1
    obj=q.find('objective');assert obj.get('type')=='Fetch' and obj.get('id')==row['parcel']
    assert obj.get('value')=='1'
    assert len(q.findall('reward'))==1 and q.find('reward').get('id')=='casinoCoin'
    notice=one('items',f"/items/item[@name='{row['notice']}']")
    assert notice.find("property[@class='Action0']/requirement[@name='PlayerLevel']").get('value')==str(row['level'])
    for name in (row['notice'],row['parcel']):
        row_recipe=next(r for r in data['recipes'] if r['name']==name)
        assert row_recipe['skill'] is None and row_recipe['station']=='delveFarmDispatch'
    checks+=8
q=one('quests',"/quests/quest[@id='delveFarmFirstHarvest']")
assert q.find("property[@name='repeatable']").get('value')=='false'
assert {r.get('id') for r in q.findall('reward')}=={'plantedCorn1','plantedChrysanthemum1'}
checks+=2
out=ROOT/'artifacts/validation';out.mkdir(parents=True,exist_ok=True)
probe=E.Element('farming')
for kind in ['recipes','stations','seeds','orders']:
    group=E.SubElement(probe,kind)
    for row in data[kind]:E.SubElement(group,'entry',**{k:str(v or '') for k,v in row.items() if not isinstance(v,dict)})
E.ElementTree(probe).write(str(out/'farming-checks.xml'),pretty_print=True)
(out/'farming-static.json').write_text(json.dumps({'checks':checks,'recipes':len(data['recipes']),'stations':len(data['stations']),'orders':len(data['orders']),'errors':[]},indent=2)+'\n')
print(f'PASS: {checks} farming checks, {len(data["recipes"])} recipes, six stations, five consuming supply orders.')
