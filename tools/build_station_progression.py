"""Additive, frozen-release crafting split with rank-bounded dependency proofs."""
from pathlib import Path
from copy import deepcopy
from lxml import etree as E
import argparse, csv, json

ROOT=Path(__file__).resolve().parents[1]
MOD='ZZZZZZZZZZDelveCraftingStations'
BASE_GAME=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
STATIONS={
 'delveFieldHearth':('Cooking','Field Hearth',{'resourceRockSmall':20,'resourceClayLump':10}),
 'delveForgeAnvil':('Smithing','Forest Forge',{'resourceRockSmall':40,'resourceClayLump':30,'resourceWood':20}),
 'delveSawKit':('Carpentry','Woodworking Bench',{'resourceWood':20,'resourceRockSmall':10,'resourceYuccaFibers':10}),
 'delveOutfittingKit':('Carpentry','Outfitting Bench',{'resourceWood':20,'resourceCloth':8,'resourceBone':4}),
 'delveMortarKit':('Alchemy','Apothecary Bench',{'resourceRockSmall':20,'resourceClayLump':10,'resourceWood':5}),
 'delveSortingTable':('Mining','Ore Sorting Table',{'resourceWood':20,'resourceRockSmall':20}),
 'delveInscriptionKit':('Alchemy','Rune Inscription Bench',{'resourceRockSmall':10,'resourceCloth':4,'resourceBone':2}),
}
SPECIAL={'delveCompostBin':'Farming','delveDryingRack':'Alchemy','delveGrainMill':'Cooking','delvePreservingCrock':'Cooking','delveFermentingBarrel':'Alchemy'}

def key(r):
 return '|'.join((r['name'].lower(),r['station'].lower(),str(r['count']),','.join(sorted(n.lower()+'='+str(c) for n,c in r['ingredients'].items()))))

def xmlkey(r):
 return key(dict(name=r.get('name'),station=r.get('craft_area',''),count=int(r.get('count','1')),ingredients={i.get('name'):int(i.get('count')) for i in r.findall('ingredient')}))

def merge(base,kind):
 doc=E.parse(str(BASE_GAME/(kind+'.xml')))
 for mod in sorted((base/'Mods').iterdir()):
  path=mod/'Config'/(kind+'.xml')
  if not path.exists():continue
  for op in E.parse(str(path)).getroot():
   if not isinstance(op.tag,str):continue
   targets=doc.xpath(op.get('xpath'))
   # Existing overlay removals can legitimately match nothing.
   if not targets and op.tag!='remove':raise AssertionError((path,op.get('xpath')))
   for t in targets:
    if op.tag=='append':
     for c in op:t.append(deepcopy(c))
    elif op.tag=='remove':
     if getattr(t,'is_attribute',False):del t.getparent().attrib[t.attrname]
     else:t.getparent().remove(t)
    elif op.tag=='set':
     if getattr(t,'is_attribute',False):t.getparent().set(t.attrname,op.text or '')
     else:t.text=op.text or ''
    elif op.tag in ('insertAfter','insertBefore'):
     for c in op:(t.addnext if op.tag=='insertAfter' else t.addprevious)(deepcopy(c))
    else:raise AssertionError(op.tag)
 return doc

def earliest(rows,sources,edges):
 levels={n:1 for n in sources}; paths={n:[] for n in sources}
 for _ in range(len(rows)+1):
  changed=False
  for r in rows:
   deps=set(r['ingredients'])|({r['station']} if r['station'] else set())|({r['tool']} if r['tool'] else set())
   if not deps<=levels.keys():continue
   stage=max([r['rank']]+[levels[d] for d in deps])
   if stage<levels.get(r['name'],999):levels[r['name']]=stage;paths[r['name']]=sorted(deps);changed=True
  for name,deps in edges.items():
   if set(deps)<=levels.keys():
    stage=max(levels[d] for d in deps)
    if stage<levels.get(name,999):levels[name]=stage;paths[name]=deps;changed=True
  if not changed:return levels,paths
 raise AssertionError('Closure did not converge')

def build(base):
 base=base.resolve();original=json.loads((base/'Catalogue/first-playtest.json').read_text(encoding='utf-8-sig'))
 # Batch 04 shipped exact runtime keys but retained the earlier JSON catalogue.
 # Reconcile only its explicit, known rune substitutions; all other drift fails.
 if (base/'Mods/ZZZZZZZDelveBatch04/Config/recipes.xml').exists():
  for r in original['recipes']:
   if r['name'] in ('delveWandRune','delveMooncapWandRune','delveEtchedWandRune','delveStaffRune','delveMooncapStaffRune','delveEtchedStaffRune'):
    metal='resourceScrapLead' if 'Wand' in r['name'] else 'resourceScrapIron'
    r['ingredients']={metal if n in ('resourceCropChrysanthemumPlant','resourceDelveMooncap','delveHerbalExtract') else n:c for n,c in r['ingredients'].items()}
    r['key']=key(r)
 original['sources']['resourceScrapLead']='Lead byproduct from Forest iron deposits: native iron boulders and iron ore each yield 5 lead when harvested'
 rows=deepcopy(original['recipes']); oldkeys={r['key'] for r in rows}
 doc=merge(base,'recipes'); native={xmlkey(r):r for r in doc.getroot().findall('recipe')}
 assert oldkeys<=native.keys(), 'Frozen catalogue and merged recipes differ'
 templates={r['key']:deepcopy(native[r['key']]) for r in rows}
 labels={}
 for file in [BASE_GAME/'Localization.csv']+sorted((base/'Mods').glob('*/Config/Localization.csv')):
  with file.open(encoding='utf-8-sig',newline='') as stream:
   for r in csv.DictReader(stream):
    if r.get('Key') and r.get('english'):labels[r['Key']]=r['english']
 for r in rows:
  r.setdefault('tool','')
  r['original_key']=r['key'];n=r['name']
  if n in STATIONS:
   r.update(rank=1,skill=STATIONS[n][0],ingredients=STATIONS[n][2].copy())
  if n in SPECIAL:r['skill']=SPECIAL[n]
  if n.startswith('armorDelve') and 'Forged' not in n:r['station']='delveForgeAnvil' if 'Heavy' in n else 'delveOutfittingKit'
  if n in ('delveIronDagger','delveIronMace','delveIronSpear'):r['station']='delveForgeAnvil'
  if n in ('delveHuntingBow','delveBorderBow'):r['station']='delveSawKit'
  if n=='delveWayfarerTea':r['station']='campfire'
  if n=='delveWardDraught':r['station']='delveMortarKit'
  if n.startswith('delveMooncap') and n.endswith('Rune'):r['station']='delveInscriptionKit'
  if n in ('delveLesserHealingPotion','delveLesserStaminaPotion'):r['station']='delveMortarKit'
  if r['station']=='delveInscriptionKit' and n in ('delveWandRune','delveStaffRune','delveTotemRune','delveHealingRune'):r['count']=30
  # Advanced cooking uses the hearth; campfire remains the field cooking route.
  if r['station']=='campfire' and r['rank']>=10:r['station']='delveFieldHearth'
  r['family']=r['station']
 for name,(skill,title,_) in STATIONS.items():
  for tier,rank in ((2,10),(3,20)):
   n=name+'Tier'+str(tier);labels[n]=('Improved ' if tier==2 else 'Masterwork ')+title
   # Construct next station at its predecessor, without consuming a placed block.
   rows.append(dict(name=n,skill=skill,rank=rank,count=1,station=name if tier==2 else name+'Tier2',family=None,tool='',
    ingredients={'resourceWood':20,'resourceRockSmall':20,'resourceCloth':4} if tier==2 else {'resourceWood':30,'resourceRockSmall':30,'resourceForgedIron':4},original_key=None))
 # Raise misleading variant gates to their actual ingredient/station stage.
 # Alternative basic field recipes keep the output available earlier.
 for _ in range(12):
  levels,paths=earliest(rows,original['sources'],original['production_edges']);changed=False
  for r in rows:
   deps=set(r['ingredients'])|({r['station']} if r['station'] else set())|({r['tool']} if r['tool'] else set())
   assert deps<=levels.keys(),(r['name'],'unreachable',deps-levels.keys())
   rank=max([r['rank']]+[levels[d] for d in deps]);assert rank<=20 or (r['name']=='thrownDynamite' and rank==40),(r['name'],rank)
   if rank!=r['rank']:r['rank']=rank;changed=True
   if r['family'] in STATIONS:
    station=r['family']+('Tier3' if rank>=20 else 'Tier2' if rank>=10 else '')
    if station!=r['station']:r['station']=station;changed=True
  if not changed:break
 else:raise AssertionError('Station/rank routing did not converge')
 levels,paths=earliest(rows,original['sources'],original['production_edges'])
 for r in rows:
  r['key']=key(r);deps=set(r['ingredients'])|({r['station']} if r['station'] else set())|({r['tool']} if r['tool'] else set())
  assert all(levels[d]<=r['rank'] for d in deps),(r['name'],'later dependency')
  r['dependency_stages']={d:levels[d] for d in sorted(deps)}
 assert len({r['key'] for r in rows})==len(rows)
 for n in STATIONS:assert levels[n]==1
 for n in ('delveWandRune','delveStaffRune','delveTotemRune','delveHealingRune','medicalBandage','delveFocusRepair','delveHideRepair','delveMetalRepair'):
  assert any(r['name']==n and not r['station'] and r['rank']==1 for r in rows),n
 out=ROOT/'src'/MOD;cfg=out/'Config';cfg.mkdir(parents=True,exist_ok=True)
 (out/'ModInfo.xml').write_text('<xml><Name value="'+MOD+'"/><DisplayName value="Forest Crafting Stations"/><Version value="0.11.0"/><Author value="Delve"/></xml>')
 recipes=E.Element('configs');append=E.Element('append',xpath='/recipes')
 for r in rows:
  if r['original_key']:
   old=templates[r['original_key']];index=list(doc.getroot()).index(native[r['original_key']])+1
   # Signature predicates avoid index shifts and leave unaudited variants untouched.
   pred="@name='%s' and @count='%s'"%(old.get('name'),old.get('count','1'))
   pred+=" and "+("@craft_area='%s'"%old.get('craft_area') if old.get('craft_area') else "not(@craft_area)")
   pred+=' and count(ingredient)='+str(len(old.findall('ingredient')))
   for i in old.findall('ingredient'):pred+=" and ingredient[@name='%s' and @count='%s']"%(i.get('name'),i.get('count'))
   xpath='/recipes/recipe['+pred+']';assert len(doc.xpath(xpath))==1,xpath
   E.SubElement(recipes,'remove',xpath=xpath);node=deepcopy(old)
   for i in node.findall('ingredient'):node.remove(i)
  else:node=E.Element('recipe',name=r['name'],craft_time='30')
  node.set('count',str(r['count']));node.attrib.pop('craft_area',None)
  if r['station']:node.set('craft_area',r['station'])
  for n,c in r['ingredients'].items():E.SubElement(node,'ingredient',name=n,count=str(c))
  append.append(node)
 recipes.append(append)
 E.ElementTree(recipes).write(str(cfg/'recipes.xml'),pretty_print=True,xml_declaration=True,encoding='utf-8')
 blocks=E.Element('configs');ba=E.SubElement(blocks,'append',xpath='/blocks')
 for iron in ('oreIronBoulder','terrOreIron'):
  harvest=E.SubElement(blocks,'append',xpath=f"/blocks/block[@name='{iron}']")
  E.SubElement(harvest,'drop',event='Harvest',name='resourceScrapLead',count='5',tag='oreWoodHarvest')
 for name,(skill,title,_) in STATIONS.items():
  labels[name]='Basic '+title
  labels[name+'Desc']=f'{skill} 1. Build by hand from early Forest supplies. Upgrade by crafting the Improved version here at {skill} 10. Earlier recipes remain available at higher station tiers.'
  for tier,rank in ((2,10),(3,20)):
   n=name+'Tier'+str(tier);b=E.SubElement(ba,'block',name=n)
   for k,v in {'Extends':name,'WorkstationName':n,'WorkstationWindow':'workstation_'+name,'DescriptionKey':n+'Desc','UnlockedBy':'','CreativeMode':'Player'}.items():E.SubElement(b,'property',name=k,value=v)
   ws=E.SubElement(b,'property',attrib={'class':'Workstation'})
   E.SubElement(ws,'property',name='Modules',value='output')
   E.SubElement(ws,'property',name='CraftingAreaRecipes',value=','.join([name]+[name+'Tier'+str(t) for t in range(2,tier+1)]))
   E.SubElement(b,'dropextendsoff');E.SubElement(b,'drop',event='Destroy',count='0')
   labels[n+'Desc']=f'{skill} {rank}. Craft at the previous station tier, then place and use. Includes all earlier {title} recipes. Prepared repair supplies still work in the field.'
 E.ElementTree(blocks).write(str(cfg/'blocks.xml'),pretty_print=True,xml_declaration=True,encoding='utf-8')
 with (cfg/'Localization.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','KeepLoaded','english'])
  for n in STATIONS:
   for k in (n,n+'Desc',n+'Tier2',n+'Tier2Desc',n+'Tier3',n+'Tier3Desc'):w.writerow([k,'Delve','','','','',labels[k]])
 catalogue={**original,'recipes':rows,'paths':paths,'earliest_stages':levels,'station_progression':STATIONS,'checks':{'result':'PASS','recipes':len(rows),'inventory':sum(not r['station'] for r in rows),'stations':len(STATIONS)*3,'later_dependencies':[]}}
 dest=ROOT/'artifacts/validation/station-progression';dest.mkdir(parents=True,exist_ok=True)
 (dest/'catalogue.json').write_text(json.dumps(catalogue,indent=2)+'\n')
 (dest/'base.txt').write_text(str(base))
 changes=[{'name':r['name'],'old':next((o for o in original['recipes'] if o['key']==r['original_key']),None),'new':r} for r in rows if r['original_key'] is None or r['key']!=r['original_key'] or r['rank']!=next(o['rank'] for o in original['recipes'] if o['key']==r['original_key'])]
 (dest/'changes.json').write_text(json.dumps(changes,indent=2))
 checks=E.Element('slice')
 for r in rows:
  node=E.SubElement(checks,'recipe',key=r['key'],name=r['name'],skill=r['skill'] or '',rank=str(r['rank']),station=r['station'])
  for n,c in r['ingredients'].items():E.SubElement(node,'ingredient',name=n,count=str(c))
 for name in STATIONS:
  for tier in (1,2,3):E.SubElement(checks,'station',name=name+('Tier'+str(tier) if tier>1 else ''),family=name,tier=str(tier))
 E.ElementTree(checks).write(str(dest/'slice-checks.xml'),pretty_print=True)
 code=['using System; using System.Collections.Generic; using HarmonyLib; namespace DelveStationProgression { public static class Catalog {', 'public static readonly Dictionary<string,int> Ranks=new Dictionary<string,int>(StringComparer.Ordinal){']
 code += ['{'+json.dumps(r['key'])+','+str(r['rank'])+'},' for r in rows];code+=['};','public static readonly Dictionary<string,string> Skills=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase){']
 groups={r['name']:r['skill'] for r in rows}
 code += ['{'+json.dumps(n)+','+(json.dumps(s) if s else 'null')+'},' for n,s in groups.items()];code+=['}; public static readonly Dictionary<string,int> Minimum=new Dictionary<string,int>(StringComparer.OrdinalIgnoreCase){']
 code += ['{'+json.dumps(n)+','+str(min(r['rank'] for r in rows if r['name']==n))+'},' for n in groups];code+=['}; public static readonly Dictionary<string,string> CoverageAliases=new Dictionary<string,string>(StringComparer.Ordinal){']
 code += ['{'+json.dumps(r['key'])+','+json.dumps(r['original_key'])+'},' for r in rows if r['name'] in ('delveBlastingPowder','thrownAmmoPipeBomb','thrownDynamite','meleeToolSalvageT1Wrench')];code+=['}; } }']
 (out/'Catalog.generated.cs').write_text('\n'.join(code))
 guide=['FOREST CRAFTING SPLIT AND STATION PROGRESSION','Proficiency gates, not character levels. No random books required.','Basic stations: proficiency 1, hand-built. Improved: 10, made at Basic. Masterwork: 20, made at Improved.','Place upgraded stations as new blocks; existing placed stations remain Basic. Higher tiers include earlier recipes.','Basic field runes/ammunition, primitive equipment, first aid and prepared repairs remain portable.','Dependency stages below include stations, tools, ingredients and collector production. Different professions may supply processed components; none is required above the recipe stage.','']
 for r in sorted(rows,key=lambda r:(r['rank'],r['skill'] or '',labels.get(r['name'],r['name']))):
  guide.append(f"P{r['rank']} {r['skill'] or 'Supplies'}: {r['count']} {labels.get(r['name'],r['name'])} | {labels.get(r['station'],r['station']) if r['station'] else 'Inventory'} | "+', '.join(f'{c} {labels.get(n,n)}' for n,c in r['ingredients'].items()))
 (dest/'CRAFTING-STATIONS.txt').write_text('\n'.join(guide)+'\n',encoding='utf-8')
 print(json.dumps(catalogue['checks']))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);a=p.parse_args();build(a.base)

