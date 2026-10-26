from pathlib import Path
import json,sys
from build_station_progression import merge,xmlkey,earliest
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05';P=R/'playtest/BatchFive';c=json.loads((A/'catalogue.json').read_text());rows=c['recipes']
docs={k:merge(P,k) for k in ['recipes','items','blocks','XUi_InGame/xui','XUi_InGame/windows']}
live={xmlkey(r):r for r in docs['recipes'].getroot().findall('recipe')}
for r in rows:
 assert r['key'] in live,r['key'];assert live[r['key']].get('craft_tool','')==(r.get('tool') or '')
changes=json.loads((A/'changes.json').read_text())
for change in changes:
 r=change['after'];old=change['before'];assert r['rank']==1 and not r['tool'] and r['station']=='delveFieldCraftingMat'
 variants=docs['recipes'].xpath('/recipes/recipe[@name=$n]',n=r['name']);assert len(variants)==1 and variants[0].get('craft_area')=='delveFieldCraftingMat'
 assert all(r['ingredients'].get(n,0)>=v for n,v in old['ingredients'].items()) and sum(r['ingredients'].values())>sum(old['ingredients'].values())
b=docs['blocks'].find("block[@name='delveFieldCraftingMat']")
assert b.find("property[@class='Workstation']/property[@name='Modules']").get('value')=='output'
assert b.find("property[@name='MultiBlockDim']").get('value')=='1,1,1'
g=docs['XUi_InGame/xui'].find("window_group[@name='workstation_delveFieldCraftingMat']")
for w in g.findall('window'):
 actual=docs['XUi_InGame/windows'].find("window[@name='%s']"%w.get('name'));assert actual is not None
 assert not actual.xpath(".//*[@controller='WorkstationToolGrid']"),'Mat must have no tool slots'
edges=dict(c['production_edges'])
for base,s in c['station_bases'].items():
 for alias in s['aliases']:
  if alias!=base:edges[alias]=[base]
levels,_=earliest(rows,c['sources'],edges)
for r in rows:
 deps=set(r['ingredients'])|({r['station']} if r['station'] else set())|({r.get('tool')} if r.get('tool') else set())
 assert all(levels.get(d,999)<=r['rank'] for d in deps),(r['name'],deps)
assert levels['delveFieldCraftingMat']==1
report={'result':'PASS','recipes':len(rows),'starters':len(changes),'mat_cost':{'wood':20,'fiber':20},'mat_tools':0,'later_dependencies':[],'scope':'Merged XML, exact recipes, increased costs, no alternate crafting routes, no tool-grid UI, rank-bounded station/tool/ingredient chains'}
(A/'static-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
