"""Fail on dead-end early perks, quest objectives or missing recipe routes."""
from pathlib import Path
from lxml import etree as E
import json, argparse
from build_forest_slice import merge
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--mods',type=Path,default=ROOT/'src')
parser.add_argument('--catalogue',type=Path,default=ROOT/'src/Forest/first-playtest.json')
args=parser.parse_args()
mods=args.mods
progress=merge(mods,'progression')
perks={p.get('name'):p for p in progress.xpath('//perk[starts-with(@name,"delvePerk")]')}
reachable=set()
def enabled(p):return not p.xpath('.//requirement[@cvar="delveNeverUnlock"]')
while True:
    before=len(reachable)
    for name,p in perks.items():
        deps={r.get('progression_name') for r in p.xpath('.//requirement[@name="ProgressionLevel"]') if r.get('progression_name','').startswith('delvePerk')}
        if enabled(p) and deps<=reachable:reachable.add(name)
    if len(reachable)==before:break
assert all(name in reachable for name,p in perks.items() if enabled(p)), 'Implemented perk stranded behind unfinished prerequisite'
early=[]
for skill in json.loads((ROOT/'src/Progression/trees.json').read_text(encoding='utf-8')):
    first=[p for p in skill['perks'] if p['rank']<=20]
    assert len(first)==5,skill['skill']
    for p in first:assert p['id'] in reachable,p['id']
    early+=first
catalog=json.loads(args.catalogue.read_text())
recipes={r['name'] for r in catalog['recipes']}
quests=merge(mods,'quests')
core=E.parse(str(mods/'Delve/Config/quests.xml'))
checked=0
for q in core.xpath('//quest[starts-with(@id,"delve")]'):
    for o in q.findall('objective'):
        if o.get('type')=='Craft':
            assert o.get('id') in recipes,(q.get('id'),'unreachable craft',o.get('id'))
            checked+=1
    for reward in q.findall('reward'):
        if reward.get('type')=='Quest':assert quests.xpath('/quests/quest[@id=$id]',id=reward.get('id'))
for skill in ('Farming','Cooking','Mining','Smithing','Carpentry','Alchemy'):
    assert 'delveLesson'+skill+'Notes' not in recipes
    notes=E.parse(str(mods/'Delve/Config/items.xml')).xpath('//item[@name=$name]',name='delveLesson'+skill+'Notes')
    assert len(notes)==1 and notes[0].xpath('property[@class="Action0"]/property[@name="QuestGiven" and @value=$id]',id='delveLesson'+skill), ('unreadable lesson',skill)
    assert notes[0].xpath('property[@name="CreativeMode" and @value="Player"]'), ('hidden lesson',skill)
    assert quests.xpath('/quests/quest[@id=$id]',id='delveLesson'+skill)
assert 'delveArborProtection' in recipes
assert catalog['checks']['blocked']==[]
report={'result':'PASS','early_perks':len(early),'reachable_enabled_perks':len(reachable),'craft_objectives':checked,'recipes':len(catalog['recipes']),'scope':'Generated dependency and quest access; runtime and human acceptance separate'}
(ROOT/'artifacts/validation/forest-access.json').write_text(json.dumps(report,indent=2))
print(report)

