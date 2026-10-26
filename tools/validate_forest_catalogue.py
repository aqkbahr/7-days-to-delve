"""Integrated XPath, ownership, recipe and dependency checks for M0/M1."""
import json
from pathlib import Path
from lxml import etree as E
from build_forest_catalogue import merged, ROOT, BASE

c=json.loads((ROOT/'src/Forest/catalogue.json').read_text())
rows=c['recipes']; resources={r['id']:r for r in c['resources']}
assert len({r['id'] for r in rows})==len(rows),'duplicate recipe id'
stations={s['id'] for s in c['stations']}; knowledge={s['id'] for s in c['knowledge']}
documents={k:merged(k) for k in ['items','blocks','buffs','entityclasses','entitygroups','quests','recipes','spawning','biomes','progression','gamestages','dialogs']}
for kind,tag in [('items','item'),('blocks','block'),('buffs','buff'),('entityclasses','entity_class'),('entitygroups','entitygroup'),('quests','quest')]:
    ns=documents[kind].getroot().findall(tag); ids=[n.get('id' if kind=='quests' else 'name') for n in ns]
    assert len(ids)==len(set(ids)),('duplicate merged definitions',kind)
known={n.get('name') for kind,tag in [('items','item'),('blocks','block')] for n in documents[kind].getroot().findall(tag)}
for r in rows:
    assert r['station'] in stations and r['knowledge'] in knowledge,r['id']
    assert r['proficiency'] in [1,10,20] and r['output_count']>0,r['id']
    assert all(i in resources and q>0 for i,q in r['inputs'].items()),r['id']
    assert r['primary_skill'] in ['Farming','Cooking','Mining','Smithing','Carpentry','Alchemy',None]
    if not r['status'].startswith('planned'):
        assert r['output'] in known,r['id']
        candidates=documents['recipes'].xpath('/recipes/recipe[@name=$n]',n=r['output'])
        assert any({i.get('name'):int(i.get('count')) for i in n.findall('ingredient')}==r['inputs'] for n in candidates),r['id']
    else:
        # Shared native output is allowed, but proposed recipe itself must not ship.
        assert not any({i.get('name'):int(i.get('count')) for i in n.findall('ingredient')}==r['inputs'] for n in documents['recipes'].xpath('/recipes/recipe[@name=$n]',n=r['output'])),r['id']

# Public live stations seed the graph; planned stations must be craftable first.
reachable={r['id'] for r in resources.values() if not r['source'].startswith('Craft through') and not r['availability'].startswith('later')}
available_stations={'inventory','campfire','forge','workbench'}
while True:
    before=len(reachable)
    for r in rows:
        if r['station'] in available_stations and set(r['inputs'])<=reachable:reachable.add(r['output'])
    available_stations |= reachable & stations
    if len(reachable)==before:break
blocked={r['output'] for r in rows}-reachable
assert not blocked,('unreachable output/circular station requirement',blocked)
assert {resources[n]['harvest_skill'] for n in ['resourceScrapIron','resourcePotassiumNitratePowder']}=={'Mining'}
mapping={r['output']:r['primary_skill'] for r in rows if not r['status'].startswith('planned')}
for item,skill in [('delveOakCudgel','Carpentry'),('delveLeatherKnuckles','Carpentry'),('resourceCloth','Carpentry'),('resourceGlue','Alchemy'),('resourceLeather','Carpentry')]:assert mapping[item]==skill
report=dict(result='PASS',recipe_variants=len(rows),live=sum(not r['status'].startswith('planned') for r in rows),
 planned=sum(r['status'].startswith('planned') for r in rows),resources=len(resources),station_types=len(stations),
 merged_config_families=len(documents),unreachable_outputs=sorted(blocked),
 scope='Static integrated source data and dependency closure, not human availability or balance acceptance')
(ROOT/'artifacts/validation/forest-catalogue.json').write_text(json.dumps(report,indent=2))
print(report)
