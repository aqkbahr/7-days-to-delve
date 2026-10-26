"""Independently validate packaged XML, stage closure, repairs and baseline retention."""
from pathlib import Path
import argparse,json,hashlib
from copy import deepcopy
from build_station_progression import merge,xmlkey,earliest,STATIONS

def audit(package,baseline,catalogue):
 rows=catalogue['recipes'];merged=merge(package,'recipes')
 bykey={xmlkey(r):r for r in merged.getroot().findall('recipe')}
 assert len({r['key'] for r in rows})==len(rows)
 for r in rows:
  assert r['key'] in bykey,r['key']
  actual=bykey[r['key']]
  assert actual.get('craft_tool','')==r['tool']
 levels,paths=earliest(rows,catalogue['sources'],catalogue['production_edges'])
 def bounded(row):
  dependencies=set(row['ingredients'])|({row['station']} if row['station'] else set())|({row['tool']} if row['tool'] else set())
  return all(levels.get(n,999)<=row['rank'] for n in dependencies)
 assert all(bounded(r) for r in rows),'Later or missing dependency'
 # Negative controls: validator must detect later facilities, tools and cycles.
 probe=deepcopy(next(r for r in rows if r['name']=='delveWandRune' and not r['station']))
 probe['station']='delveInscriptionKitTier3';assert not bounded(probe)
 probe['station']='';probe['tool']='delveSawKitTier2';assert not bounded(probe)
 cyclic=[dict(name='cycleA',rank=1,ingredients={'cycleB':1},station='',tool=''),dict(name='cycleB',rank=1,ingredients={'cycleA':1},station='',tool='')]
 assert 'cycleA' not in earliest(cyclic,[],{})[0]
 definitions={}
 for kind,tag in (('blocks','block'),('items','item')):
  definitions.update({n.get('name'):n for n in merge(package,kind).getroot().findall(tag)})
 def props(name,trail=()):
  name=name.split(':')[0];assert name not in trail,('Inheritance cycle',name)
  node=definitions[name];parent=node.find("property[@name='Extends']")
  result=props(parent.get('value'),trail+(name,)) if parent is not None else {}
  result.update({p.get('name'):p.get('value') for p in node.findall('property') if p.get('name')})
  return result
 for iron in ('oreIronBoulder','terrOreIron'):
  drops=definitions[iron].findall("drop[@event='Harvest'][@name='resourceScrapLead']")
  assert any(d.get('count')=='5' for d in drops),('Missing early lead supply',iron)
 repairs=0
 for r in rows:
  for resource in props(r['name']).get('RepairTools','').split(','):
   if resource:assert levels.get(resource,999)<=r['rank'],(r['name'],'later repair',resource);repairs+=1
 for family in STATIONS:
  assert levels[family]==1
  for tier in (2,3):
   name=family+'Tier'+str(tier);node=definitions[name]
   assert levels[name]==(10 if tier==2 else 20)
   areas=node.find("property[@class='Workstation']/property[@name='CraftingAreaRecipes']").get('value').split(',')
   assert areas==[family]+[family+'Tier'+str(i) for i in range(2,tier+1)]
 # The user's combined content is frozen. No replaced core, map, art or other module.
 retained=0
 for folder in ('Mods','Worlds'):
  for source in (baseline/folder).rglob('*'):
   if not source.is_file():continue
   target=package/source.relative_to(baseline)
   assert target.is_file() and hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(target.read_bytes()).digest(),str(target)
   retained+=1
 return {'result':'PASS','recipes':len(rows),'inventory':sum(not r['station'] for r in rows),'stage_counts':{str(stage):sum(r['rank']<=stage for r in rows) for stage in range(1,21)},'repair_bindings':repairs,'baseline_files_retained':retained,'negative_controls':['late station','late tool','cyclic dependency'],'later_dependencies':[]}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 report=audit(a.package,a.baseline,json.loads((a.package/'Catalogue/first-playtest.json').read_text(encoding='utf-8-sig')))
 a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report))
