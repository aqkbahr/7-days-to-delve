from pathlib import Path
from copy import deepcopy
from lxml import etree as E
import json,csv
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
release=Path((ROOT/'artifacts/skill-coverage-base.txt').read_text(encoding='utf-8-sig').strip())
out=ROOT/'src/ZZZZZZZZZDelveSkillCoverage';(out/'Config').mkdir(parents=True,exist_ok=True)
evidence=ROOT/'artifacts/validation/skill-coverage';evidence.mkdir(parents=True,exist_ok=True)
def apply(d,patch):
 for op in patch:
  if not isinstance(op.tag,str):continue
  targets=d.xpath(op.get('xpath'));assert targets,(op.tag,op.get('xpath'))
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
docs={}
for kind in ('items','blocks','recipes','loot','traders','quests'):
 d=E.parse(str(BASE/(kind+'.xml')))
 for mod in sorted((release/'Mods').iterdir()):
  f=mod/'Config'/(kind+'.xml')
  if f.exists():apply(d,E.parse(str(f)).getroot())
 docs[kind]=d
patches={k:E.Element('configs') for k in docs}
def op(kind,tag,path):return E.SubElement(patches[kind],tag,xpath=path)
def prop(n,k,v):E.SubElement(n,'property',name=k,value=str(v))
rows=[dict(name='delveBlastingPowder',skill='Alchemy',rank=10,station='delveMortarKit',count=5,ingredients={'resourceCoal':2,'resourcePotassiumNitratePowder':3}),
 dict(name='thrownAmmoPipeBomb',skill='Alchemy',rank=20,station='delveMortarKit',count=1,ingredients={'delveBlastingPowder':5,'resourceForgedIron':2,'resourceCloth':1}),
 dict(name='thrownDynamite',skill='Alchemy',rank=40,station='delveMortarKit',count=1,ingredients={'delveBlastingPowder':15,'resourceCloth':3,'delveHerbalSpirit':2}),
 dict(name='meleeToolSalvageT1Wrench',skill='Smithing',rank=20,station='delveForgeAnvil',count=1,ingredients={'resourceForgedIron':12,'resourceLeather':4,'resourceWood':4})]
a=op('items','append','/items');item=E.SubElement(a,'item',name='delveBlastingPowder')
for k,v in {'Extends':'resourceGunPowder','CustomIcon':'resourceGunPowder','CreativeMode':'Player','DescriptionKey':'delveBlastingPowderDesc','Tags':'resource,delveReagent,delveAlchemy','UnlockedBy':''}.items():prop(item,k,v)
for row in rows:
 name=row['name']
 if docs['recipes'].xpath('/recipes/recipe[@name=$n]',n=name):op('recipes','remove',f"/recipes/recipe[@name='{name}']")
 recipe=E.SubElement(op('recipes','append','/recipes'),'recipe',name=name,count=str(row['count']),craft_time='30',craft_area=row['station'])
 for k,v in row['ingredients'].items():E.SubElement(recipe,'ingredient',name=k,count=str(v))
 row['key']='|'.join([name.lower(),row['station'].lower(),str(row['count']),','.join(sorted(k.lower()+'='+str(v) for k,v in row['ingredients'].items()))])
 if name!='delveBlastingPowder':
  path=f"/items/item[@name='{name}']"
  for attr in ('UnlockedBy','DescriptionKey'):
   if docs['items'].xpath(path+f"/property[@name='{attr}']"):op('items','remove',path+f"/property[@name='{attr}']")
  a=op('items','append',path);prop(a,'UnlockedBy','');prop(a,'DescriptionKey',name+'DelveCoverageDesc')

# New-world equipment has an explicit craft/use path. Keep all item definitions
# for old saves, schematics and compatibility; remove unsupported supply entries.
catalogue=json.loads((release/'Catalogue/first-playtest.json').read_text(encoding='utf-8-sig'))
allowed={r['name'].split(':')[0] for r in catalogue['recipes']}|{r['name'] for r in rows}
items={i.get('name'):i for i in docs['items'].xpath('/items/item')}
def props(n,seen=None):
 seen=set() if seen is None else seen
 assert n not in seen,n;seen.add(n);it=items[n];parent=it.find("property[@name='Extends']")
 values=props(parent.get('value'),seen) if parent is not None and parent.get('value') in items else {}
 values.update({p.get('name'):p.get('value') for p in it.findall('property') if p.get('name')});return values
removed=[];audit=[]
for name,it in items.items():
 p=props(name);tags=set(p.get('Tags','').split(','))
 equipment=bool(tags&{'weapon','tool','ammo','gun','heavyArmor','mediumArmor','lightArmor','vehicle'}) or name.startswith(('gun','meleeTool','meleeWpn','thrown','ammo','armor','vehicle'))
 if not equipment:continue
 keep=name in allowed
 # Books, schematics and native technical templates are never an equipment drop.
 if 'schematic' in name.lower() or 'master' in name.lower():continue
 if not keep:removed.append(name)
 audit.append(dict(item=name,status='integrated' if keep else 'removed-from-new-supply',reason='Enabled recipe and existing tree' if keep else 'Outside supported equipment roster; definition retained for saves'))
source_counts={}
if removed:
 predicate=' or '.join("@name='%s'"%n for n in removed)
 for kind in ('loot','traders'):
  matches=docs[kind].xpath('//item['+predicate+']');source_counts[kind]=len(matches)
  if matches:op(kind,'remove','//item['+predicate+']')
  preview=deepcopy(docs[kind]);apply(preview,patches[kind])
  for g in preview.xpath('//lootgroup | //trader_item_group'):
   if not g.findall('item') and docs[kind].xpath(f"//{g.tag}[@name='{g.get('name')}']/item"):
    E.SubElement(op(kind,'append',f"//{g.tag}[@name='{g.get('name')}']"),'item',name='resourceScrapIron',count='2,5')
 rewards=0;ids=set()
 for r in docs['quests'].xpath('//reward'):
  if r.get('id') in removed:
   ids.add(r.get('id'));copy=deepcopy(r);copy.set('id','casinoCoin');copy.set('type','Item');copy.set('value','100');op('quests','append',docs['quests'].getpath(r.getparent())).append(copy);rewards+=1
 if ids:op('quests','remove','//reward['+' or '.join("@id='%s'"%n for n in ids)+']')
 source_counts['quest_rewards']=rewards
for kind,patch in patches.items():
 if len(patch):
  apply(docs[kind],patch);E.ElementTree(patch).write(str(out/'Config'/(kind+'.xml')),encoding='utf-8',xml_declaration=True,pretty_print=True)
for kind in ('loot','traders'):
 assert not [n for n in docs[kind].xpath('//item') if n.get('name') in removed]
sources=set(catalogue['sources'])|{r['name'] for r in catalogue['recipes']}|{r['name'] for r in rows}
for r in rows:assert set(r['ingredients'])|{r['station']}<=sources,(r['name'],'unreachable supply')
code=['using System;namespace DelveCoverage { public static class CoverageCatalog { public sealed class Row {public string Name,Key,Skill;public int Rank; public Row(string n,string k,string s,int r){Name=n;Key=k;Skill=s;Rank=r;}} public static readonly Row[] Rows={']
for r in rows:code.append('new Row('+','.join(json.dumps(r[k]) for k in ('name','key','skill'))+','+str(r['rank'])+'),')
code+=['};public static Row Find(string key){foreach(var r in Rows)if(r.Key==key)return r;return null;}public static Row ByName(string name){foreach(var r in Rows)if(String.Equals(name,r.Name,StringComparison.OrdinalIgnoreCase))return r;return null;} } }']
(ROOT/'src/SkillCoverage/CoverageCatalog.generated.cs').write_text('\n'.join(code))
loc=[('delveBlastingPowder','Alchemical blasting powder'),('delveBlastingPowderDesc','Alchemy 10 at the Mortar Kit. Reagent for blast and excavation charges.'),('thrownAmmoPipeBomb','Alchemical blast charge'),('thrownDynamite','Alchemical excavation charge'),('thrownAmmoPipeBombDelveCoverageDesc','Alchemy 20 at the Mortar Kit. Light, then throw. Enemy damage trains Alchemy; +0.5% damage per proficiency above 1. Native fuse and friendly-fire rules apply.'),('thrownDynamiteDelveCoverageDesc','Alchemy 40 at the Mortar Kit. A powerful excavation explosive. Enemy damage trains Alchemy; +0.5% damage per proficiency above 1. Native terrain damage and fuse apply.'),('meleeToolSalvageT1WrenchDelveCoverageDesc','Smithing 20 at the Forest Forge. Metal salvage trains Smithing; +0.25% salvage damage per proficiency above 1. Attacking enemies trains Blunt. Repair with ordinary repair supplies.')]
with (out/'Config/Localization.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
 for k,v in loc:w.writerow([k,'items','Item','false','false',v])
(out/'ModInfo.xml').write_text('<xml><Name value="DelveSkillCoverage"/><DisplayName value="Delve Skill Coverage"/><Version value="1.0.0"/><Author value="Delve"/></xml>')
(evidence/'recipes.json').write_text(json.dumps(rows,indent=2));(evidence/'equipment-audit.json').write_text(json.dumps(audit,indent=2))
(evidence/'static.json').write_text(json.dumps(dict(result='PASS',recipes=len(rows),equipment=len(audit),removed_sources=source_counts,base=str(release)),indent=2))
print((evidence/'static.json').read_text())
