"""Apply every mod XPath to a copy of vanilla and validate content references.

This does not replace an actual engine startup or multiplayer playtest.
"""
import argparse
import copy
import csv
import json
from pathlib import Path
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--game',default='D:/Steam/steamapps/common/7 Days To Die')
args=parser.parse_args()
base=Path(args.game)/'Data/Config'
mod=ROOT/'src/Delve/Config'
merged={}
errors=[]
patch_count=0
for path in sorted(mod.glob('*.xml')):
    doc=E.parse(str(base/path.name))
    for operation in E.parse(str(path)).getroot():
        if operation.tag=='set' and not (operation.text or '').strip():
            errors.append(f'{path.name}: engine rejects an empty set; remove the property instead')
        targets=doc.xpath(operation.get('xpath'))
        if not targets:
            errors.append(f'{path.name}: unmatched XPath {operation.get("xpath")}')
        for target in targets:
            if operation.tag=='append':
                for child in operation: target.append(copy.deepcopy(child))
            elif operation.tag=='set':
                if getattr(target,'is_attribute',False):
                    target.getparent().set(target.attrname,operation.text or '')
                else: target.text=operation.text or ''
            elif operation.tag=='remove': target.getparent().remove(target)
            else: errors.append(f'Unsupported validator operation: {operation.tag}')
        patch_count+=1
    merged[path.stem]=doc

def ids(doc,tag,attr='name'):
    values=[n.get(attr) for n in doc.getroot().findall(tag)]
    if len(values)!=len(set(values)):
        errors.append(f'Duplicate {tag} identifiers')
    return set(values)

items=ids(merged['items'],'item')
blocks=ids(merged['blocks'],'block')
entities=ids(merged['entityclasses'],'entity_class')
buffs=ids(merged['buffs'],'buff')
quests=ids(merged['quests'],'quest','id')
progression={n.get('name') for n in merged['progression'].xpath('//attribute|//skill|//perk|//crafting_skill')}
with (mod/'Localization.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f))
texts={r['Key'] for r in rows}
if len(texts)!=len(rows): errors.append('Duplicate localization keys')

def require(value,valid,context):
    if value not in valid: errors.append(f'{context}: missing reference {value}')

for n in E.parse(str(mod/'items.xml')).xpath('//item'):
    require(n.get('name'),texts,'item title')
    for p in n.xpath('property[@name="Extends"]'): require(p.get('value'),items,'item parent')
    for p in n.xpath('.//property[@name="QuestGiven"]'): require(p.get('value'),quests,'quest item')
for n in E.parse(str(mod/'recipes.xml')).xpath('//recipe'):
    require(n.get('name'),items|blocks,'recipe output')
    for ingredient in n: 
        if ingredient.tag=='ingredient': require(ingredient.get('name'),items|blocks,'ingredient')
for n in E.parse(str(mod/'entityclasses.xml')).xpath('//entity_class'):
    require(n.get('extends'),entities,'entity parent')
    for drop in n.xpath('drop'): require(drop.get('name'),items|blocks,'harvest drop')
for n in E.parse(str(mod/'entitygroups.xml')).xpath('//e'): require(n.get('n'),entities,'entity group')
for n in E.parse(str(mod/'quests.xml')).xpath('//quest'):
    for objective in n.xpath('objective'): require(objective.get('id'),items|blocks,'quest objective')
    for reward in n.xpath('reward'):
        if reward.get('type')=='Item': require(reward.get('id'),items|blocks,'quest reward')
        if reward.get('type')=='Quest': require(reward.get('id'),quests,'next quest')
for path in mod.glob('*.xml'):
    doc=E.parse(str(path))
    for fx in doc.xpath('//triggered_effect[@action="AddBuff"]'):
        for name in fx.get('buff').split(','): require(name,buffs,'buff trigger')
    for n in doc.xpath('//*[@parent]'): require(n.get('parent'),progression,'progression parent')
    for n in doc.xpath('//*[@name_key]|//*[@desc_key]|//*[@description_key]|//*[@long_desc_key]'):
        for a in ['name_key','desc_key','description_key','long_desc_key']:
            if n.get(a,'').startswith('delve'): require(n.get(a),texts,'localization')

# Reject nonexistent effect names against metadata from the actual game assembly.
api_path=ROOT/'artifacts/inspection/passive-effects.json'
if api_path.exists():
    valid=set(json.loads(api_path.read_text(encoding='utf-8-sig')))
    for path in mod.glob('*.xml'):
        for fx in E.parse(str(path)).xpath('//passive_effect'):
            require(fx.get('name'),valid,'passive effect')
else: errors.append('Missing passive-effects.json: run Export-Api.ps1 first')

# Integration invariants: separate attributes must never charge/refund native
# talent currency; every authored skill status must exist from initialization.
attribute_nodes=merged['progression'].xpath("//attribute[starts-with(@name,'delveAtt')]")
if len(attribute_nodes)!=6: errors.append('Expected six Delve attributes')
for a in attribute_nodes:
    if a.get('min_level')!='1' or a.get('max_level')!='20': errors.append('Invalid attribute range: '+a.get('name'))
    if a.get('override_cost')!=','.join(['0']*20): errors.append('Attribute would mix native talent currency: '+a.get('name'))
    levels={n.get('level') for n in a.xpath('effect_group/effect_description')}
    if levels!={str(i) for i in range(1,21)}: errors.append('Missing rank description: '+a.get('name'))
skill_names=['Blades','Blunt','Polearms','Archery','Wands','Staffs','Totems','Unarmed','HeavyArmor','MediumArmor','LightArmor','PackMule','Athletics','Stealth','Farming','Cooking','Mining','Smithing','Carpentry','Alchemy']
for skill in skill_names: require('delveSkill'+skill,buffs,'proficiency status')
for stat in ('HealthMax','StaminaMax'):
    if merged['buffs'].xpath(f"//passive_effect[@name='{stat}'][@value='@$PlayerLevelBonus']"):
        errors.append('Native automatic growth would duplicate Constitution: '+stat)
level=merged['progression'].getroot().find('level')
if level.get('max_level')!='80' or level.get('skill_points_per_level')!='1': errors.append('Wrong character advancement budget')

# All catalog choices have one rank/point and real proficiency prerequisites.
from progression_content import enrich
catalog=enrich(json.loads((ROOT/'src/Progression/trees.json').read_text(encoding='utf-8')))
for tree in catalog:
    for perk in tree['perks']:
        nodes=merged['progression'].xpath("//perk[@name=$name]",name=perk['id'])
        if len(nodes)!=1:
            errors.append('Missing/duplicate catalog perk: '+perk['id']); continue
        n=nodes[0]
        if n.get('max_level')!='1' or n.get('override_cost')!='1':errors.append('Wrong talent price/ranks: '+perk['id'])
        if not n.xpath("level_requirements/requirement[@name='CVarCompare'][@cvar=$c][@value=$v]",c='delveLevel'+tree['skill'],v=str(perk['rank'])):errors.append('Missing proficiency gate: '+perk['id'])
        if not perk['implemented'] and not n.xpath("level_requirements/requirement[@cvar='delveNeverUnlock']"):errors.append('Incomplete talent could charge points: '+perk['id'])
if merged['quests'].xpath("//reward[@type='SkillPoints'][number(@value)>0]"):errors.append('Non-level talent rewards remain')

# Horde pools must preserve the engine's counts/timing/caps and stay isolated
# from ordinary POI spawning. Check actual merged output, not generator helpers.
group_nodes={n.get('name'):n for n in merged['entitygroups'].xpath('/entitygroups/entitygroup')}
native_stages=E.parse(str(base/'gamestages.xml'))
stages=merged['gamestages'].xpath("/gamestages/spawner[@name='BloodMoonHorde']/gamestage")
for stage in stages:
    old=native_stages.xpath("/gamestages/spawner[@name='BloodMoonHorde']/gamestage[@stage=$s]",s=stage.get('stage'))[0]
    for actual,original in zip(stage.findall('spawn'),old.findall('spawn')):
        require(actual.get('group'),group_nodes,'blood moon pool')
        if {k:v for k,v in actual.attrib.items() if k!='group'} != {k:v for k,v in original.attrib.items() if k!='group'}:
            errors.append('Horde count/timing/concurrency changed')
        if int(stage.get('stage'))<=40:
            pool=group_nodes[actual.get('group')]
            total=sum(float(n.get('p','1')) for n in pool.findall('e'))
            corrupted=sum(float(n.get('p','1')) for n in pool.findall('e') if n.get('n','').startswith('delve'))
            if abs(corrupted/total-.2)>.00001: errors.append('Early horde must be 20% Delve by weight')
        elif actual.get('group')!=original.get('group'): errors.append('Later horde changed outside first-slice scope')
for name,pool in group_nodes.items():
    if name.startswith('delve'):
        for enemy in pool.findall('e'): require(enemy.get('n'),entities,'reusable enemy pool')

report={'xpath_operations':patch_count,'localization_entries':len(texts),'errors':errors,
        'scope':'Static XML, reference and game-effect validation; not a runtime or multiplayer pass.'}
out=ROOT/'artifacts/validation'; out.mkdir(parents=True,exist_ok=True)
(out/'content-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for error in errors: print('ERROR:',error)
print(f'{patch_count} XPath operations; {len(texts)} localized entries; {len(errors)} errors.')
raise SystemExit(bool(errors))
