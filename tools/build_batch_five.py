"""Frozen-release Batch 5: field mat and a coherent starter equipment step."""
from pathlib import Path
from copy import deepcopy
import sys,json,csv
from lxml import etree as E
from build_station_progression import merge,key,earliest
R=Path(__file__).resolve().parents[1]; A=R/'artifacts/batch-05';A.mkdir(parents=True,exist_ok=True)
B=Path((A/'base.txt').read_text(encoding='utf-8-sig').strip())
M=R/'src/ZZZZZZZZZZZDelveBatch05';C=M/'Config';C.mkdir(parents=True,exist_ok=True)
catalog=json.loads((B/'Catalogue/first-playtest.json').read_text(encoding='utf-8-sig'));rows=catalog['recipes']
items=merge(B,'items');recipes=merge(B,'recipes')
patch={k:E.Element('configs') for k in ['items','blocks','recipes','XUi_InGame/xui']}
def op(kind,tag,xpath):return E.SubElement(patch[kind],tag,xpath=xpath)
def prop(node,n,v):return E.SubElement(node,'property',name=n,value=str(v))
def fx(node,n,v,operation='base_set',**kw):return E.SubElement(node,'passive_effect',name=n,operation=operation,value=str(v),**kw)
costs={
 'delveBoneDagger':{'resourceBone':8,'resourceYuccaFibers':10},
 'delveOakCudgel':{'resourceWood':25,'resourceYuccaFibers':10},
 'delveAshSpear':{'resourceWood':25,'resourceRockSmall':12,'resourceYuccaFibers':10},
 'delveLeatherKnuckles':{'resourceLeather':6,'resourceYuccaFibers':10},
 'delveBorderBow':{'resourceWood':30,'resourceYuccaFibers':20},
}
for n in ['delveStarterWand','delveStarterStaff','delveStarterTotem','delveMendingTotem']:costs[n]={'resourceWood':30,'resourceCloth':8,'resourceRockSmall':15}
armor={'Light':(10,{'resourceCloth':12,'resourceYuccaFibers':15}),'Padded':(11,{'resourceCloth':16,'resourceLeather':6}),'Medium':(12,{'resourceLeather':12,'resourceCloth':6}),'Heavy':(14,{'resourceScrapIron':45,'resourceLeather':6})}
for category,(rating,cost) in armor.items():
 for slot in ['Helmet','Outfit','Gloves','Boots']:costs['armorDelve'+category+slot]=cost.copy()
changes=[];loc={}
baseline_loc={}
for file in sorted((B/'Mods').glob('*/Config/Localization.csv')):
 with file.open(encoding='utf-8-sig',newline='') as f:
  for entry in csv.DictReader(f):
   if entry.get('Key') and entry.get('english'):baseline_loc[entry['Key']]=entry['english']
for name in ('delveArrivalDesc','delveFieldGuideDesc'):
 loc[name]='First craft and place a Field Crafting Mat from 20 plant fibers and 20 wood. All Delve starter weapons and armor are made there; primitive vanilla gear and field supplies can still be made by hand. '+baseline_loc[name]
for row in rows:
 if row['name'] not in costs:continue
 changes.append({'before':deepcopy(row)})
 n=row['name'];row.update(ingredients=costs[n],station='delveFieldCraftingMat',tool='',rank=1);row['key']=key(row)
 changes[-1]['after']=deepcopy(row)
 op('recipes','remove',f"/recipes/recipe[@name='{n}']")
 recipe=E.SubElement(op('recipes','append','/recipes'),'recipe',name=n,count='1',craft_time='30',craft_area='delveFieldCraftingMat')
 for ingredient,count in costs[n].items():E.SubElement(recipe,'ingredient',name=ingredient,count=str(count))
 assert sum(r['name']==n for r in rows)==1,n
assert len(changes)==25
row=dict(name='delveFieldCraftingMat',skill='Carpentry',rank=1,count=1,station='',tool='',ingredients={'resourceYuccaFibers':20,'resourceWood':20});row['key']=key(row);rows.append(row)
recipe=E.SubElement(op('recipes','append','/recipes'),'recipe',name=row['name'],count='1',craft_time='15')
for n,c in row['ingredients'].items():E.SubElement(recipe,'ingredient',name=n,count=str(c))
b=E.SubElement(op('blocks','append','/blocks'),'block',name='delveFieldCraftingMat')
for n,v in {'Extends':'workbench','Shape':'ModelEntity','Model':'#@modfolder:Resources/fieldmat.unity3d?delveFieldCraftingMat','MultiBlockDim':'1,1,1','ModelOffset':'0,0,0','CustomIcon':'delveFieldCraftingMat','CustomIconTint':'FFFFFF','TintColor':'FFFFFF','DescriptionKey':'delveFieldCraftingMatDesc','UnlockedBy':'','WorkstationName':'delveFieldCraftingMat','WorkstationWindow':'workstation_delveFieldCraftingMat','HeatMapStrength':'0','EconomicValue':'0','SellableToTrader':'false','MaxDamage':'200'}.items():prop(b,n,v)
ws=E.SubElement(b,'property',attrib={'class':'Workstation'});prop(ws,'Modules','output');prop(ws,'CraftingAreaRecipes','delveFieldCraftingMat')
repair=E.SubElement(b,'property',attrib={'class':'RepairItems'});prop(repair,'resourceYuccaFibers',5)
E.SubElement(b,'dropextendsoff');E.SubElement(b,'drop',event='Destroy',count='0')
native=E.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/XUi_InGame/xui.xml')
group=deepcopy(native.find("window_group[@name='workstation_workbench']"));group.set('name','workstation_delveFieldCraftingMat');op('XUi_InGame/xui','append','/xui').append(group)
loc['delveFieldCraftingMat']='Field Crafting Mat';loc['delveFieldCraftingMatDesc']='Carpentry 1. A one-metre woven mat for all Delve starter weapons and armor. No add-on slots, fuel or recipe tools. Build by hand from 20 plant fibers and 20 wood. Advanced gear still needs specialist stations.'
for n in list(costs)[:5]:
 path=f"/items/item[@name='{n}']"
 op('items','set',path+"/effect_group[@name='Delve crafted weapon']/passive_effect[@name='EntityDamage']/@value").text='0.25'
 eg=E.SubElement(op('items','append',path),'effect_group',name='Batch 5 reinforced starter');fx(eg,'DegradationMax',.25,'perc_add')
 loc[n+'Desc']='Starter gear: craft at the Field Crafting Mat. +25 percentage points damage and +25% durability over the native primitive foundation; original attack speed, stamina and reach. Specialist stations produce the next tier.'
# A bone blade should not depend on metal to repair.
op('items','set',"/items/item[@name='delveBoneDagger']/property[@name='RepairTools']/@value").text='resourceBone'
for n in ['delveStarterWand','delveStarterStaff','delveStarterTotem','delveMendingTotem']:
 path=f"/items/item[@name='{n}']";op('items','set',path+"/effect_group/passive_effect[@name='DegradationMax']/@value").text='300'
 if n!='delveMendingTotem':
  eg=E.SubElement(op('items','append',path),'effect_group',name='Batch 5 focus');fx(eg,'EntityDamage',.10,'perc_add')
 else:op('items','set',path+"/effect_group/passive_effect[@name='MagazineSize']/@value").text='5'
 loc[n+'Desc']='Field Crafting Mat starter focus; 300 durability. '+('Five healing runes per load; restores 20 base health per cast.' if n=='delveMendingTotem' else 'Adds 10 percentage points direct damage to matching basic runes; original capacity and spell effects.')+' Crafted from 30 wood, 8 cloth and 15 stone. Forged focuses remain the next specialist-station tier.'
for category,(rating,cost) in armor.items():
 for slot in ['Helmet','Outfit','Gloves','Boots']:
  n='armorDelve'+category+slot;path=f"/items/item[@name='{n}']"
  for stat,value in [('PhysicalDamageResist',rating),('ElementalDamageResist',rating),('DegradationMax',300)]:op('items','set',path+f"/effect_group/passive_effect[@name='{stat}']/@value").text=str(value)
  loc[n+'Desc']=f'Field Crafting Mat starter armor. {rating} physical and heat/electrical armor per piece, 300 durability. Retains its weight-class movement, stamina and noise tradeoffs. No set bonus.'
for category,rating in [('Light',13),('Medium',16),('Heavy',19)]:
 for slot in ['Helmet','Outfit','Gloves','Boots']:
  n='armorDelveForged'+category+slot
  for stat in ['PhysicalDamageResist','ElementalDamageResist']:op('items','set',f"/items/item[@name='{n}']/effect_group/passive_effect[@name='{stat}']/@value").text=str(rating)
  loc[n+'Desc']=f'Forged {category.lower()} armor. {rating} armor per piece, 400 durability. Proficiency 20 at its specialist station with the required add-on. Retains weight-class penalties.'
op('items','set',"/items/item[@name='delveForgedKnuckles']/effect_group[@name='Forged handling']/passive_effect[@name='EntityDamage']/@value").text='.50'
loc['delveForgedKnucklesDesc']='Reinforced Handwraps: proficiency 20 at the Outfitting Bench with Armor-Fitting Form. +55 percentage points damage over native leather knuckles, 400 durability. A clear upgrade from mat-crafted handwraps.'
for kind,root in patch.items():
 file=C/(kind+'.xml');file.parent.mkdir(parents=True,exist_ok=True);E.indent(root);E.ElementTree(root).write(str(file),encoding='utf-8',xml_declaration=True)
with (C/'Localization.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
 for n,v in loc.items():w.writerow([n,'Delve','','','',v])
(M/'ModInfo.xml').write_text('<xml><Name value="DelveBatch05"/><DisplayName value="Delve Batch 5 - Field Crafting"/><Version value="0.13.0"/><Author value="Delve"/></xml>')
edges=deepcopy(catalog['production_edges'])
for base,spec in catalog['station_bases'].items():
 for alias in spec['aliases']:
  if alias!=base:edges[alias]=[base]
levels,paths=earliest(rows,catalog['sources'],edges)
for r in rows:
 deps=set(r['ingredients'])|({r['station']} if r['station'] else set())|({r.get('tool')} if r.get('tool') else set())
 assert all(levels.get(d,999)<=r['rank'] for d in deps),(r['name'],deps)
 r['dependency_stages']={d:levels[d] for d in sorted(deps)}
catalog.update(recipes=rows,earliest_stages=levels,paths=paths)
catalog['station_bases']['delveFieldCraftingMat']={'title':'Field Crafting Mat','skill':'Carpentry','aliases':['delveFieldCraftingMat'],'tools':[]}
catalog['checks']={'result':'PASS','recipes':len(rows),'moved_starters':25,'later_dependencies':[]}
(A/'catalogue.json').write_text(json.dumps(catalog,indent=2));(A/'changes.json').write_text(json.dumps(changes,indent=2))
code=['using System; namespace DelveBatchFive { public static class Catalog { public sealed class Row {public string Key,Name,Skill;public int Rank;public Row(string k,string n,string s,int r){Key=k;Name=n;Skill=s;Rank=r;}} public static readonly Row[] Rows={']
for r in rows:
 if r['name'] in costs or r['name']=='delveFieldCraftingMat':code.append('new Row('+','.join(json.dumps(r[k]) for k in ['key','name','skill'])+','+str(r['rank'])+'),')
code.append('}; public static Row Find(string k){foreach(var r in Rows)if(r.Key==k)return r;return null;} public static Row ByName(string n){foreach(var r in Rows)if(String.Equals(r.Name,n,StringComparison.OrdinalIgnoreCase))return r;return null;} } }')
(M/'Catalog.generated.cs').write_text('\n'.join(code))
# Retain all previous regression cases, with updated exact keys.
checks=E.parse(str(B/'Evidence/StationAddons/checks.xml'))
for e in list(checks.getroot().findall('recipe')):checks.getroot().remove(e)
for r in rows:E.SubElement(checks.getroot(),'recipe',key=r['key'],skill=r['skill'] or '',rank=str(r['rank']),tool=r.get('tool') or '',queue=str(bool(r.get('tool'))).lower())
checks.write(str(A/'checks.xml'),pretty_print=True)
print(json.dumps(catalog['checks']))

