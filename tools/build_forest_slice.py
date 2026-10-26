"""Strict live-only Forest closure. Stations and tools must themselves be reachable.

No planned rows, trader stock, public workbenches, smelter units or arbitrary
resource declarations are admitted as starting nodes. Writes runtime recipe gates
and a release catalogue from the same verified recipe signatures.
"""
from pathlib import Path
from copy import deepcopy
from lxml import etree as E
import argparse, json, csv
from forest_readiness import NATIVE

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
MOD_NAMES=['Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest','ZDelveRecruits']

def merge(mods,kind):
    doc=E.parse(str(BASE/(kind+'.xml')))
    for mod in MOD_NAMES:
        path=mods/mod/'Config'/(kind+'.xml')
        if not path.exists():continue
        for op in E.parse(str(path)).getroot():
            targets=doc.xpath(op.get('xpath'));assert targets,(path,op.get('xpath'))
            for t in targets:
                if op.tag=='append':
                    for c in op:t.append(deepcopy(c))
                elif op.tag=='set':
                    if getattr(t,'is_attribute',False):t.getparent().set(t.attrname,op.text or '')
                    else:t.text=op.text or ''
                elif op.tag=='remove':t.getparent().remove(t)
                elif op.tag in ('insertBefore','insertAfter'):
                    for c in op:(t.addprevious if op.tag=='insertBefore' else t.addnext)(deepcopy(c))
                else:raise AssertionError(op.tag)
    return doc

def signature(r):
    ins=sorted(i.get('name').lower()+'='+str(int(i.get('count'))) for i in r.findall('ingredient'))
    return '|'.join([r.get('name').lower(),r.get('craft_area','').lower(),r.get('count','1'),','.join(ins)])

def build(mods):
    docs={k:merge(mods,k) for k in ('recipes','items','blocks','biomes')}
    metadata={}
    for file in ('pantry.json','processing.json','forged.json','readiness.json'):
        for row in json.loads((ROOT/'src/Forest'/file).read_text())['recipes']:metadata[row['name']]=(row['skill'],row.get('rank',20))
    for row in json.loads((ROOT/'src/Farming/first-pass.json').read_text())['recipes']:
        metadata.setdefault(row['name'],(row['skill'],row['rank']))
    metadata.update({n:(s,r) for n,(s,r) in NATIVE.items()})
    def owner(name):
        if name.startswith('delveLesson') and name.endswith('Notes'):return None,1
        if name=='delveArborProtection':return 'Alchemy',20
        if name in ('delveRecruitLedger','delveRallyFlag','delveRecoveryShrine'):return 'Carpentry',1
        if name in metadata:return metadata[name]
        if name.startswith('delveHeritage') or name in ('delveFieldGuide','delveForestReadinessGuide'):return None,1
        if name in ('delveIronDagger','delveIronMace','delveIronSpear'):return 'Smithing',20
        if name=='delveHuntingBow':return 'Carpentry',20
        if name in ('delveThornhide','delveGloomPelt'):return 'Farming',1
        if name=='delveForestCrystal':return 'Mining',1
        if name.startswith('armorDelve'):return ('Smithing' if 'Heavy' in name else 'Carpentry'),1
        if name=='delveBoneDagger':return 'Smithing',1
        if name in ('delveOakCudgel','delveAshSpear','delveLeatherKnuckles','delveBorderBow') or any(w in name for w in ('Wand','Staff','Totem')):return 'Carpentry',1
        if name in ('delveHealingPoultice','delveWardDraught'):return 'Alchemy',1
        if name=='delveWayfarerTea':return 'Cooking',1
        raise AssertionError(('Missing owner',name))
    authored=set()
    for mod in MOD_NAMES:
        file=mods/mod/'Config/recipes.xml'
        if file.exists():authored.update(signature(r) for r in E.parse(str(file)).xpath('//append/recipe'))
    rows=[]; seen=set()
    for r in docs['recipes'].getroot().findall('recipe'):
        name=r.get('name');key=signature(r)
        if key not in authored and name not in NATIVE:continue
        skill,rank=owner(name)
        if rank>20:continue
        # Native variants of an advertised output may require a different,
        # inaccessible facility; only explicit inventory variants are admitted.
        if key not in authored and r.get('craft_area','') not in ('','campfire'):continue
        assert 'learnable' not in r.get('tags','').split(','),(name,'random book requirement')
        assert not r.findall('wildcard_forge_category')
        assert key not in seen,('duplicate signature',key)
        seen.add(key)
        rows.append(dict(key=key,name=name,skill=skill,rank=rank,count=int(r.get('count','1')),
                         station=r.get('craft_area',''),tool=r.get('craft_tool',''),
                         ingredients={i.get('name'):int(i.get('count')) for i in r.findall('ingredient')}))
    # Explicit acquisition evidence, independently audited against world/native data.
    sources={
        'resourceWood':'Forest trees; native renewable tree seeds',
        'resourceYuccaFibers':'Common Forest grass',
        'resourceRockSmall':'Surface stones and Forest stone deposits',
        'resourceClayLump':'Forest soil dug with the craftable stone shovel',
        'resourceScrapIron':'19 marked Forest iron deposits; native iron harvest',
        'resourcePotassiumNitratePowder':'19 marked Forest nitrate deposits',
        'resourceCoal':'19 marked Forest coal deposits',
        'foodRottingFlesh':'Forest zombie/wildlife remains',
        'foodRawMeat':'Forest deer/rabbits/boar and other native wildlife',
        'resourceAnimalFat':'Forest animal harvesting',
        'resourceBone':'Forest animal/zombie harvesting',
        'resourceLeather':'Forest animal harvesting; also crafted plant-based leather',
        'resourceFeather':'Native Forest bird nests; fiber-fletched ammo is a deterministic alternative',
        'foodHoney':'Guaranteed one honey on destroying a native Forest stump',
        'delveThornhide':'Forest Thornback harvest; optional conversion',
        'delveGloomPelt':'Forest Gloomcat harvest; optional conversion',
        'delveForestCrystal':'Forest Crystal Stag harvest; optional conversion',
    }
    pantry=json.loads((ROOT/'src/Forest/pantry.json').read_text())
    forest_blocks={e['block'] for e in pantry['biomes']['pine_forest']}
    blocks={n.get('name'):n for n in docs['blocks'].getroot().findall('block')}
    for name in sorted(forest_blocks):
        assert docs['biomes'].xpath("//biome[@name='pine_forest']//decoration[@blockname=$name]",name=name),name
        for drop in blocks[name].findall("drop[@event='Harvest']"):
            product=drop.get('name')
            if product and not product.startswith('planted'):sources[product]='Wild Forest '+name+'; starter gardens and renewable cultivation'
    assert blocks['treeStump'].find("drop[@name='foodHoney'][@prob='1']") is not None
    deposits=json.loads((ROOT/'src/Worlds/Allium/resource-sites.json').read_text())
    for mineral in ('iron','nitrate','coal'):
        assert any(d['resource']==mineral and d['region_index']==0 for d in deposits),mineral
    # No station is magically present. Work forward from raw gathering only.
    reachable=set(sources); paths={n:[] for n in sources}; pending=list(rows)
    rounds=0
    while True:
        rounds+=1;progress=False
        for row in pending[:]:
            required=set(row['ingredients'])|({row['station']} if row['station'] else set())|({row['tool']} if row['tool'] else set())
            if not required<=reachable:continue
            if row['name'] not in reachable:
                reachable.add(row['name']);paths[row['name']]=sorted(required);progress=True
            pending.remove(row)
        # Native collector operation is a production edge, not an assumed water source.
        if 'drinkJarRiverWater' not in reachable and {'delveRainCollector','drinkJarEmpty'}<=reachable:
            reachable.add('drinkJarRiverWater');paths['drinkJarRiverWater']=['delveRainCollector','drinkJarEmpty'];progress=True
        if not progress:break
    blocked=[dict(name=r['name'],missing=sorted((set(r['ingredients'])|({r['station']} if r['station'] else set())|({r['tool']} if r['tool'] else set()))-reachable)) for r in pending]
    assert not blocked,json.dumps(blocked,indent=2)
    # Check identities and station module dependencies after inheritance resolution.
    all_items={n.get('name'):n for n in docs['items'].getroot().findall('item')}
    definitions={**blocks,**all_items}
    def props(name,seen=None):
        seen=set() if seen is None else seen
        assert name not in seen,('inheritance cycle',name);seen.add(name)
        item=definitions[name.split(':')[0]];parent=item.find("property[@name='Extends']")
        p=props(parent.get('value'),seen) if parent is not None else {}
        p.update({n.get('name'):n.get('value') for n in item.findall('property') if n.get('name')})
        return p
    for row in rows:
        for n in [row['name'],*row['ingredients']]:assert n.split(':')[0] in definitions,n
        if row['station'] and row['station']!='campfire':
            station=blocks[row['station']]
            assert station.find("property[@class='Workstation']/property[@name='Modules']").get('value')=='output',row
        repair=props(row['name']).get('RepairTools','')
        if repair:assert set(repair.split(','))<=reachable,(row['name'],'inaccessible repair',repair)
    # Native base building uses upgrade/repair actions rather than recipe rows.
    # Prove the advertised wood -> cobblestone fortification loop as well.
    def group(name,kind):
        node=blocks[name];parent=node.find("property[@name='Extends']")
        result=group(parent.get('value'),kind) if parent is not None else {}
        result.update({n.get('name'):n.get('value') for n in node.findall("property[@class='%s']/property"%kind)})
        return result
    upgrades=[];repairs={}
    assert 'meleeToolRepairT0StoneAxe' in reachable
    for name,target in [('frameShapes','woodShapes'),('woodShapes','cobblestoneShapes')]:
        action=group(name,'UpgradeBlock')
        assert action['ToBlock']==target and action['Item'] in reachable,(name,action)
        upgrades.append(dict(block=name,to=target,item=action['Item'],count=int(action['ItemCount']),tool='meleeToolRepairT0StoneAxe'))
    for name in ('frameShapes','woodShapes','cobblestoneShapes','oldWoodDoor','woodHatch','ladderWood','cntWoodWritableCrate','campfire'):
        repair=group(name,'RepairItems')
        assert repair and set(repair)<=reachable,(name,repair)
        repairs[name]={n:int(v) for n,v in repair.items()}
    output={'scope':'Forest first playtest: exact live recipe variants through proficiency 20','sources':sources,
            'production_edges':{'drinkJarRiverWater':['delveRainCollector','drinkJarEmpty']},'recipes':rows,'paths':paths,
            'base_upgrades':upgrades,'base_repairs':repairs,
            'checks':{'result':'PASS','recipes':len(rows),'raw_sources':len(sources),'closure_rounds':rounds,'base_upgrades':len(upgrades),'base_repairs':len(repairs),'blocked':blocked}}
    (ROOT/'src/Forest/first-playtest.json').write_text(json.dumps(output,indent=2)+'\n')
    labels={}
    for file in [BASE/'Localization.csv',mods/'Delve/Config/Localization.csv']:
        with file.open(encoding='utf-8-sig',newline='') as stream:
            for entry in csv.DictReader(stream):
                if entry.get('Key') and entry.get('english'):labels[entry['Key']]=entry['english']
    def label(n):return labels.get(n,labels.get(n.split(':')[0],n))
    guide=['FOREST FIRST PLAYTEST - COMPLETE LIVE RECIPE CATALOGUE',
           'Allium-v0.10 / 7 Days to Die 3.3.0 (b18)',
           f'{len(rows)} exact recipe variants; quantities below are base recipe quantities.',
           'Required rank is crafting proficiency, not character level.',
           'Only these recipes and native scrapping are enabled in this playtest.',
           'All inputs, stations, tools, repair supplies and base upgrades have Forest acquisition paths.',
           'No trader purchase, random recipe book or later biome is required.','']
    for skill in ('Farming','Cooking','Mining','Smithing','Carpentry','Alchemy',None):
        owned=sorted((r for r in rows if r['skill']==skill),key=lambda r:(r['rank'],label(r['name']),r['key']))
        guide+=['%s (%d variants)'%(skill or 'Guides and settlement paperwork',len(owned))]
        for r in owned:
            inputs=', '.join('%d %s'%(v,label(n)) for n,v in r['ingredients'].items())
            guide.append('  P%d: %d %s <- %s [%s%s]'%(r['rank'],r['count'],label(r['name']),inputs,label(r['station']) if r['station'] else 'Inventory',('; tool: '+label(r['tool'])) if r['tool'] else ''))
        guide.append('')
    guide+=['FOREST RAW SOURCES']+['  '+label(n)+': '+v for n,v in sorted(sources.items())]
    guide+=['','BASE BUILDING (STONE AXE UPGRADE/REPAIR ACTION)']
    guide+=['  %s -> %s: %d %s'%(label(r['block']),label(r['to']),r['count'],label(r['item'])) for r in upgrades]
    guide+=['  Repair '+label(n)+': '+', '.join('%d %s'%(v,label(k)) for k,v in costs.items()) for n,costs in repairs.items()]
    (ROOT/'docs/forest-ready-catalogue.txt').write_text('\n'.join(guide)+'\n',encoding='utf-8')
    groups={}
    for row in rows:
        if row['name'] in groups:assert groups[row['name']][0]==row['skill']
        groups[row['name']]=(row['skill'],min(groups.get(row['name'],('',100))[1],row['rank']))
    code=['// Generated by build_forest_slice.py; exact live variants, no optimistic fallbacks.',
          'using System; using System.Collections.Generic; namespace Delve { public static class ForestSliceCatalog {',
          'public static string Key(Recipe r) { var ins=new List<string>(); foreach(var i in r.ingredients)ins.Add(i.itemValue.ItemClass.GetItemName().ToLowerInvariant()+"="+i.count);ins.Sort(StringComparer.Ordinal);return r.GetName().ToLowerInvariant()+"|"+(r.craftingArea??"").ToLowerInvariant()+"|"+r.count+"|"+String.Join(",",ins.ToArray());}',
          'public static int Rank(Recipe r) { switch(Key(r)) {']
    for row in rows:code.append('case '+json.dumps(row['key'])+':return '+str(row['rank'])+';')
    code+=['default:return 21;} }','public static int Minimum(string n) { switch((n??"").ToLowerInvariant()) {']
    for name,(_,rank) in groups.items():code.append('case '+json.dumps(name.lower())+':return '+str(rank)+';')
    code+=['default:return 21;} }','public static string Skill(string n) { switch((n??"").ToLowerInvariant()) {']
    for name,(skill,_) in groups.items():code.append('case '+json.dumps(name.lower())+':return '+('null' if skill is None else json.dumps(skill))+';')
    code+=['default:return null;} } } }']
    (ROOT/'src/Code/ForestSliceCatalog.generated.cs').write_text('\n'.join(code)+'\n')
    checks=E.Element('slice')
    for row in rows:E.SubElement(checks,'recipe',key=row['key'],name=row['name'],skill=row['skill'] or '',rank=str(row['rank']))
    out=ROOT/'artifacts/validation/forest-ready';out.mkdir(parents=True,exist_ok=True)
    E.ElementTree(checks).write(str(out/'slice-checks.xml'),pretty_print=True)
    (out/'closure.json').write_text(json.dumps(output['checks'],indent=2)+'\n')
    print(output['checks'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mods',type=Path,default=ROOT/'src');a=p.parse_args();build(a.mods)
