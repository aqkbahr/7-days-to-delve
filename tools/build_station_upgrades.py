"""Generate an additive station consolidation without changing saved block IDs."""
from pathlib import Path
from copy import deepcopy
import json,csv
from lxml import etree as E
from station_upgrade_design import BASES,UPGRADES,COLLECTOR,RETIRED,tool,requirement
ROOT=Path(__file__).resolve().parents[1]
BASE=Path((ROOT/'artifacts/station-upgrades/base.txt').read_text(encoding='utf-8-sig').strip())
OUT=ROOT/'src/ZZZZZZZZZZDelveStations';CFG=OUT/'Config';CFG.mkdir(parents=True,exist_ok=True)
NATIVE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
def merge(kind,include_new=False):
    doc=E.parse(str(NATIVE/(kind+'.xml')))
    for mod in sorted(list((BASE/'Mods').iterdir())+([OUT] if include_new else []),key=lambda p:p.name.lower()):
        path=mod/'Config'/(kind+'.xml')
        if not path.exists():continue
        for op in E.parse(str(path)).getroot():
            if not isinstance(op.tag,str):continue
            targets=doc.xpath(op.get('xpath'));assert targets or op.tag=='remove',(path,op.get('xpath'))
            for t in targets:
                if op.tag=='append':
                    for c in op:t.append(deepcopy(c))
                elif op.tag=='set':
                    if getattr(t,'is_attribute',False):t.getparent().set(t.attrname,op.text or '')
                    else:t.text=op.text or ''
                elif op.tag=='remove':
                    if getattr(t,'is_attribute',False):del t.getparent().attrib[t.attrname]
                    else:t.getparent().remove(t)
                elif op.tag in ('insertBefore','insertAfter'):
                    for c in op:(t.addprevious if op.tag=='insertBefore' else t.addnext)(deepcopy(c))
                else:raise AssertionError(op.tag)
    return doc
def key(row):return '|'.join([row['name'].lower(),row.get('station','').lower(),str(row['count']),','.join(sorted(k.lower()+'='+str(v) for k,v in row['ingredients'].items()))])
def prop(parent,name,value):return E.SubElement(parent,'property',name=name,value=str(value))
patch={k:E.Element('configs') for k in ('blocks','items','recipes','XUi_InGame/xui','XUi_InGame/windows')}
def op(kind,tag,xpath):return E.SubElement(patch[kind],tag,xpath=xpath)
def upsert(kind,xpath,name,value):
    existing={'blocks':blocks,'items':items}.get(kind)
    if existing is None or existing.xpath(xpath+"/property[@name='"+name+"']"):
        op(kind,'remove',xpath+"/property[@name='"+name+"']")
    prop(op(kind,'append',xpath),name,value)
loc={'delveStationUpgradeHeading':'ADD-ONS'}
catalog=json.loads((BASE/'Catalogue/first-playtest.json').read_text(encoding='utf-8-sig'))
rows=deepcopy(catalog['recipes']);extras=[];changed=[]
live=merge('recipes');blocks=merge('blocks');items=merge('items')
def recipe(row):
    r=E.SubElement(op('recipes','append','/recipes'),'recipe',name=row['name'],count=str(row['count']),craft_time=str(row.get('seconds',20)))
    if row.get('station'):r.set('craft_area',row['station'])
    if row.get('tool'):r.set('craft_tool',row['tool'])
    for n,c in row['ingredients'].items():E.SubElement(r,'ingredient',name=n,count=str(c))
    row['key']=key(row);extras.append(row)
    return r
for name,(title,skill,aliases,tools,cost) in BASES.items():
    for variant in [name]+[a for a in aliases if a in RETIRED]:
        path="/blocks/block[@name='"+variant+"']"
        ws=path+"/property[@class='Workstation']"
        upsert('blocks',ws,'Modules','tools,output')
        upsert('blocks',ws,'CraftingAreaRecipes',','.join(aliases))
        upsert('blocks',path,'WorkstationWindow','workstation_'+name)
        upsert('blocks',path,'WorkstationName',name)
        upsert('blocks',path,'DescriptionKey',variant+'Desc')
        if variant in RETIRED:upsert('blocks',path,'CreativeMode','None')
        loc[variant]=title+(' (Legacy)' if variant in RETIRED else '')
        loc[variant+'Desc']=f'{skill} base station. Install removable add-ons in its tool slots: '+', '.join(UPGRADES[t][0]+' ('+str(UPGRADES[t][2])+')' for t in tools)+'. Proficiency and recipe ingredients still apply. Existing station variants remain usable.'
    op('recipes','remove',"/recipes/recipe[@name='"+name+"']")
    rows=[r for r in rows if r['name']!=name]
    recipe(dict(name=name,skill=skill,rank=1,count=1,ingredients=cost,station='',tool=''))
    group=deepcopy(E.parse(str(NATIVE/'XUi_InGame/xui.xml')).find("window_group[@name='workstation_workbench']"))
    group.set('name','workstation_'+name)
    group.insert(3,E.Element('window',name='delveTools_'+name))
    op('XUi_InGame/xui','remove',"/xui/window_group[@name='workstation_"+name+"']")
    op('XUi_InGame/xui','append','/xui').append(group)
    window=deepcopy(E.parse(str(NATIVE/'XUi_InGame/windows.xml')).find("window[@name='windowToolsForge']"))
    window.set('name','delveTools_'+name)
    grid=window.find('.//grid');grid.set('cols',str(len(tools)));grid.set('required_tools',','.join(tool(t) for t in tools))
    window.find('.//label').set('text_key','delveStationUpgradeHeading')
    op('XUi_InGame/windows','append','/windows').append(window)
for name in RETIRED:
    op('recipes','remove',"/recipes/recipe[@name='"+name+"']")
    rows=[r for r in rows if r['name']!=name]
# Update only audited recipe variants; stable old crafting-area aliases let
# native recipe gates, quest objectives and stored queues keep their identity.
for row in rows:
    needed=requirement(row)
    if needed==row.get('tool',''):continue
    matches=[]
    for r in live.xpath('/recipes/recipe[@name=$n]',n=row['name']):
        probe=dict(name=r.get('name'),station=r.get('craft_area',''),count=int(r.get('count','1')),ingredients={i.get('name'):int(i.get('count')) for i in r.findall('ingredient')})
        if key(probe)==row['key']:matches.append(r)
    assert len(matches)==1,(row['name'],len(matches))
    replacement=deepcopy(matches[0]);replacement.set('craft_tool',needed)
    # Match exact recipe attributes/ingredients, not all alternative recipes.
    r=matches[0];selector="/recipes/recipe[@name='%s' and @count='%s' and %s and count(ingredient)=%d"%(row['name'],r.get('count','1'),"@craft_area='%s'"%row['station'] if row['station'] else 'not(@craft_area)',len(row['ingredients']))
    for n,c in row['ingredients'].items():selector+=" and ingredient[@name='%s' and @count='%s']"%(n,c)
    selector+=']'
    op('recipes','remove',selector);op('recipes','append','/recipes').append(replacement)
    row['tool']=needed;changed.append(row)
for k,(title,skill,rank,cost,icon,function) in UPGRADES.items():
    name=tool(k)
    if name.startswith('delveUpgrade'):
        it=E.SubElement(op('items','append','/items'),'item',name=name)
        for n,v in {'Extends':'resourceScrapIron','CustomIcon':icon,'DescriptionKey':name+'Desc','UnlockedBy':'','CreativeMode':'Player','Stacknumber':1,'EconomicValue':0,'SellableToTrader':'false'}.items():prop(it,n,v)
    loc[name]=title;loc[name+'Desc']=f'{skill} {rank}. '+function+'. Install in the matching workstation add-on slot; carrying it in your backpack is not enough. Removable and reusable.'
    recipe(dict(name=name,skill=skill,rank=rank,count=1,ingredients=cost,station='',tool=''))
for name,(title,rank,cost,function) in COLLECTOR.items():
    loc[name]=title;loc[name+'Desc']=f'Farming {rank}. '+function+'. Install in the Forest Rain Collector.'
    recipe(dict(name=name,skill='Farming',rank=rank,count=1,ingredients=cost,station='',tool=''))
loc['delveRainCollectorDesc']='Farming 1. Place outside under open sky and supply empty jars. Farming 10 adds a Catchment Funnel and Raincloth Canopy; Farming 20 adds a Charcoal Water Filter. Install upgrades in the collector slots.'
# Update instructions against the final combined localization, preserving lesson
# objectives and optional-tome behavior while removing obsolete station advice.
oldloc={}
for file in sorted((BASE/'Mods').glob('*/Config/Localization.csv')):
    for r in csv.DictReader(file.open(encoding='utf-8-sig')):
        if r.get('english'):oldloc[r['Key']]=r['english']
replacements={
    'in a Compost Bin':'at a Farm Workbench with a Compost Basket',
    'at a Herb Drying Rack':'at an Apothecary Bench with a Herb-Drying Attachment',
    'at the Mortar Kit':'at the Apothecary Bench',
    'proficiency 10 opens an Apothecary Bench':'proficiency 10 opens Apothecary add-ons',
    'Mining proficiency 10 opens a Sorting Table':'Mining proficiency 10 opens the Stone-Cutting Set for the Ore Processing Table',
    'Use Knowledge Notes for step-by-step help.':'Optional Crafting Tomes cost 500 gold from traders and provide step-by-step lessons.',
}
for k,v in oldloc.items():
    if k in loc:continue
    revised=v
    for before,after in replacements.items():revised=revised.replace(before,after)
    if revised!=v:loc[k]=revised
loc['delveProcessingGuideDesc']='Build base stations at proficiency 1. Install removable add-ons in their ADD-ONS slots at proficiency 10 and 20; backpack tools do not enable station recipes. Farming: Farm Workbench and Rain Collector. Cooking: Field Hearth and Pantry Bench. Smithing: Forest Forge. Carpentry: Carpenter and Outfitting benches. Alchemy: Apothecary and Rune benches. Mining: Ore Processing Table. Basic water and meals need no hearth tool; advanced meals require a pot or grill. See STATION-UPGRADES.txt for the full progression.'
loc['delveForestReadinessGuideDesc']='Forest recipes use crafting proficiency 1-20, independent of character level. Gather wood, stone, grass, clay and marked ores. Build a refuge with doors and spikes; prepare weapons, armor, ammunition/runes, medicine, food and repair supplies. Build base stations at proficiency 1 and install specialized add-ons at 10 and 20. Gardens supply plants and seeds; wildlife supplies meat, hides and bone. Collect rainwater in clay jars and boil it at the Field Hearth. All recipes through 20 remain available within the Forest. See STATION-UPGRADES.txt for station tools and ingredient routes.'
# Efficient variants are genuinely new capabilities for the Farming20 add-on.
for original in list(rows):
    if original['skill']!='Farming' or not original['name'].startswith('planted') or original['rank']>20:continue
    row=deepcopy(original);row.update(rank=20,count=2,station='delveFarmDispatch',tool=tool('SeedPress'))
    row['ingredients']={n:3 if c==2 and n!='resourceClayLump' else c for n,c in row['ingredients'].items()}
    recipe(row)
# A collector remains the second Farming base, with its existing native mechanics.
for original in list(rows):
    if original.get('station')=='delveInscriptionKit' and original['rank']==1:
        row=deepcopy(original);row.update(rank=10,count=original['count']*2,tool=tool('EngravingTools'))
        recipe(row)
for row in rows:
    if row['name']=='delveRainCollector':
        row['skill']='Farming';extras.append(deepcopy(row))
rows=[r for r in rows if r['key'] not in {e['key'] for e in extras}]+extras
for row in rows:row['key']=key(row)
# Resolve stations and tool prerequisites, not just ingredient names.
aliasbase={a:n for n,(_,_,aliases,_,_) in BASES.items() for a in aliases}
available=set(catalog['sources']);pending=[r for r in rows if r['rank']<=20];rounds=0
# The current spell update uses lead. Its existing Forest deposit sites are
# present in the packaged world even though the older source list omitted it.
sites=json.loads((BASE/'resource-sites.json').read_text(encoding='utf-8-sig'))
assert any(s['resource']=='lead' and s['region_index']==0 for s in sites)
assert blocks.xpath("/blocks/block[@name='terrOreLead']/drop[@name='resourceScrapLead' and @event='Harvest']")
catalog['sources']['resourceScrapLead']='Existing marked Forest lead deposits (native lead-ore harvest)'
available.add('resourceScrapLead')
while pending:
    if {'delveRainCollector','drinkJarEmpty'}<=available:available.add('drinkJarRiverWater')
    unlocked=[]
    for r in pending:
        station=aliasbase.get(r.get('station',''),r.get('station',''))
        if set(r['ingredients'])<=available and (not station or station in available) and (not r.get('tool') or r['tool'] in available):unlocked.append(r)
    if not unlocked:break
    available.update(r['name'] for r in unlocked);pending=[r for r in pending if r not in unlocked];rounds+=1
assert not pending,[(r['name'],r.get('tool'),r.get('station')) for r in pending]
catalog.update(recipes=rows,station_bases={n:dict(title=t,skill=s,aliases=a,tools=[tool(x) for x in ts]) for n,(t,s,a,ts,_) in BASES.items()},station_addons={tool(k):dict(title=v[0],skill=v[1],rank=v[2],function=v[5]) for k,v in UPGRADES.items()})
catalog['station_addons'].update({n:dict(title=v[0],skill='Farming',rank=v[1],function=v[3]) for n,v in COLLECTOR.items()})
catalog.pop('station_progression',None)
catalog['station_upgrade_model']=dict(mode='installed_addons',base_rank=1,addon_ranks=[10,20],legacy_variants=RETIRED)
catalog['coverage_note']=f'{len(rows)-1} variants through proficiency 20; the preserved Alchemy-40 excavation charge is outside the first-playtest scope.'
# Recompute published dependency metadata for physical bases and installed tools.
def deps(r):
    return set(r['ingredients'])|({aliasbase.get(r['station'],r['station'])} if r.get('station') else set())|({r['tool']} if r.get('tool') else set())
levels={n:1 for n in catalog['sources']};paths={n:[] for n in levels}
for _ in range(len(rows)+1):
    updated=False
    for r in rows:
        needed=deps(r)
        if not needed<=levels.keys():continue
        stage=max([r['rank']]+[levels[n] for n in needed])
        if stage<levels.get(r['name'],999):levels[r['name']]=stage;paths[r['name']]=sorted(needed);updated=True
    for n,needed in catalog['production_edges'].items():
        if set(needed)<=levels.keys():
            stage=max(levels[d] for d in needed)
            if stage<levels.get(n,999):levels[n]=stage;paths[n]=needed;updated=True
    if not updated:break
for r in rows:
    r['dependency_stages']={n:levels[n] for n in sorted(deps(r))}
    assert all(stage<=r['rank'] for stage in r['dependency_stages'].values()),r['key']
    r['base_station']=aliasbase.get(r.get('station'),r.get('station')) or ''
catalog.update(earliest_stages=levels,paths=paths)
catalog['checks'].update(result='PASS',recipes=len(rows),inventory=sum(not r.get('station') for r in rows),stations=9,raw_sources=len(catalog['sources']),closure_rounds=rounds,blocked=[],station_bases=10,addon_recipes=len(UPGRADES)+len(COLLECTOR))
for kind,root in patch.items():
    p=CFG/(kind+'.xml');p.parent.mkdir(parents=True,exist_ok=True);E.ElementTree(root).write(str(p),pretty_print=True,encoding='utf-8',xml_declaration=True)
with (CFG/'Localization.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
    for k,v in loc.items():w.writerow([k,'DelveStations','','','',v])
(OUT/'ModInfo.xml').write_text('<xml><Name value="ZZZZZZZZZZDelveStations"/><DisplayName value="Delve Station Upgrades"/><Version value="0.12.0"/><Author value="Delve"/></xml>')
ART=ROOT/'artifacts/station-upgrades'
(ART/'catalogue.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
(ART/'design.json').write_text(json.dumps(dict(bases=BASES,upgrades=UPGRADES,collector=COLLECTOR,retired=RETIRED,extras=extras,changed=changed),indent=2),encoding='utf-8')
# Small independent gate supplement; the tested core and prior compatibility
# modules remain unchanged. Existing exact recipe signatures are preserved.
code=['using System; namespace DelveStations { public class Row { public string Name,Skill; public int Rank; public Row(string n,string s,int r){Name=n;Skill=s;Rank=r;} } public static class Catalog { public static Row Find(string key){switch(key){']
for row in extras:code.append('case '+json.dumps(row['key'])+':return new Row('+json.dumps(row['name'])+','+json.dumps(row['skill'])+','+str(row['rank'])+');')
code+=['default:return null;}} public static Row ByName(string name){switch((name??" ").Trim().ToLowerInvariant()){']
for name in sorted({r['name'] for r in extras if r['name'] in BASES or r['name'].startswith('delveUpgrade') or r['name'] in COLLECTOR or r['name']=='delveRainCollector'}):
    r=min((r for r in extras if r['name']==name),key=lambda x:x['rank']);code.append('case '+json.dumps(name.lower())+':return new Row('+json.dumps(name)+','+json.dumps(r['skill'])+','+str(r['rank'])+');')
code+=['default:return null;}}}}']
(ROOT/'src/StationUpgrades/Catalog.generated.cs').write_text('\n'.join(code))
print(json.dumps(catalog['checks']));print('Changed tool requirements:',len(changed),'Extra/updated recipe signatures:',len(extras))
