"""Build a standalone late-loading enemy module over the validated Delve release.
Does not regenerate or overwrite the in-progress advancement overhaul.
"""
from pathlib import Path
from xml.etree import ElementTree as E
from copy import deepcopy
import json, csv, argparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'src/ZDelveForest'; CFG=OUT/'Config'; CFG.mkdir(parents=True,exist_ok=True)
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
parser=argparse.ArgumentParser();parser.add_argument('--base-release');args=parser.parse_args()
pin=ROOT/'artifacts/forest-base-release.txt'
release=Path(args.base_release) if args.base_release else Path((pin if pin.exists() else ROOT/'dist/latest-allium-release.txt').read_text(encoding='utf-8-sig').strip())
(ROOT/'artifacts/forest-current-build-base.txt').write_text(str(release),encoding='utf-8')
roster=json.loads((ROOT/'src/Forest/roster.json').read_text())
texts={}
def node(container,tag,**attrs): return E.SubElement(container,tag,{k:str(v) for k,v in attrs.items()})
def prop(parent,name,value): return node(parent,'property',name=name,value=value)
def fx(parent,name,value,operation='base_set'): return node(parent,'passive_effect',name=name,operation=operation,value=value)
def patch(name):
    root=E.Element('configs'); return root,node(root,'append',xpath='/'+name)
def save(path,root):
    E.indent(root); E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

entities,ea=patch('entity_classes'); items,ia=patch('items'); recipes,ra=patch('recipes'); buffs,ba=patch('buffs')
for e in roster:
    key=e['id']; texts[key]=e['name']; texts[key+'Desc']=e['role']
    node(ea,'color',name=key+'Color',value=e['color'])
    # Existing six enemies/boss keep the same identifiers and save compatibility.
    if 'harvest' not in e:
        # Replace only the authored entity, never its vanilla parent.
        node(entities,'remove',xpath=f"/entity_classes/entity_class[@name='{key}']")
        en=node(entities,'append',xpath='/entity_classes'); en=node(en,'entity_class',name=key,extends=e['parent'])
    else: en=node(ea,'entity_class',name=key,extends=e['parent'])
    prop(en,'UserSpawnType','Menu'); prop(en,'SizeScale',e['size']);prop(en,'ExperienceGain',e['xp'])
    # MatColor requires the zombie alternate-material assets. Animals do not
    # supply them; use a guarded per-renderer color block on those models.
    prop(en,'DelveTint' if e['parent'].startswith('animal') else 'MatColor',e['color'] if e['parent'].startswith('animal') else key+'Color')
    prop(en,'MoveSpeedAggro',e['speed']);prop(en,'TimeStayAfterDeath',300)
    prop(en,'HandItem',key+'Attack')
    if key=='delveAshboundWarden':prop(en,'LootDropProb',1)
    if 'harvest' not in e:
        prop(en,'Tags','entity,zombie,walker,delveCorrupted')
        node(en,'drop',event='Harvest',name='delveEmberSalts',count=12 if key=='delveAshboundWarden' else 1 if key=='delveImp' else 2)
    else: node(en,'drop',event='Harvest',name=e['harvest'],count=e['count'])
    if key=='delveCrystalStag': prop(en,'MoveSpeedPanic',2)
    if key=='delveThornbackBoar': prop(en,'IsEnemyEntity','true')
    eg=node(en,'effect_group',name='Base Effects');fx(eg,'HealthMax',e['hp']);fx(eg,'PhysicalDamageResist',e['armor'])
    attack=node(ia,'item',name=key+'Attack');prop(attack,'Extends','meleeHandMaster');prop(attack,'CreativeMode','None')
    # Preserve native animal/zombie animation handling while explicitly balancing damage.
    prop(attack,'HoldType',35 if e['parent'].startswith('animal') else 9)
    act=node(attack,'property',**{'class':'Action0'})
    for p,v in [('DamageEntity',e['damage']),('DamageBlock',e['block']),('Delay',e['delay']),('Range',e['reach'])]:prop(act,p,v)
    eg=node(attack,'effect_group',name=key+'Attack',tiered='false')
    fx(eg,'EntityDamage',e['damage']);fx(eg,'BlockDamage',e['block']);fx(eg,'AttacksPerMinute',round(60/e['delay'],3));fx(eg,'DamageFalloffRange',e['reach'])
    texts[key+'Attack']=e['name']+' attack'

for key,title,icon,color,value,product,count in [
    ('delveThornhide','Thornhide','resourceLeather','98,135,66',18,'resourceLeather',3),
    ('delveGloomPelt','Gloom Pelt','resourceLeather','90,67,119',30,'resourceLeather',5),
    ('delveForestCrystal','Forest Crystal','resourceRockSmall','99,211,244',40,'delveEmberSalts',3)]:
    item=node(ia,'item',name=key);prop(item,'Extends',icon);prop(item,'CustomIcon',icon);prop(item,'CustomIconTint',color)
    prop(item,'DescriptionKey',key+'Desc');prop(item,'EconomicValue',value);prop(item,'Stacknumber',100)
    texts[key]=title;texts[key+'Desc']=f'Harvested from magical Forest wildlife. Trade it or craft {count} '+('Ember Salts.' if product=='delveEmberSalts' else 'leather.')
    r=node(ra,'recipe',name=product,count=count,craft_time=8);node(r,'ingredient',name=key,count=1)

for key,title,seconds,speed,damage in [('delveForestBrace','Bracing',2,-.75,-.5),('delveForestRush','Rush',4,.45,.25),('delveForestSpent','Recovering',5,-.6,-.5)]:
    b=node(ba,'buff',name=key,name_key=key,description_key=key+'Desc',icon='ui_game_symbol_skull')
    node(b,'stack_type',value='replace');node(b,'duration',value=seconds)
    eg=node(b,'effect_group');fx(eg,'WalkSpeed',speed,'perc_add');fx(eg,'RunSpeed',speed,'perc_add');fx(eg,'EntityDamage',damage,'perc_add')
    texts[key]=title;texts[key+'Desc']='Heavy enemy attack phase. Make space when it braces; counterattack during recovery.'

groups,ga=patch('entitygroups');spawning=E.Element('configs')
native=E.parse(BASE/'entitygroups.xml')
def clone(source,name,mix):
    g=deepcopy(native.find(f"./entitygroup[@name='{source}']"));assert g is not None,source
    g.set('name',name); total=sum(float(e.get('p','1')) for e in g.findall('e'));portion=1-sum(mix.values())
    live=sum(float(e.get('p','1')) for e in g.findall('e') if e.get('n')!='none')/total
    for e in g.findall('e'):e.set('p',str(float(e.get('p','1'))/total*(1 if e.get('n')=='none' else portion)))
    for enemy,weight in mix.items():node(g,'e',n=enemy,p=weight*live)
    ga.append(g)
for source,mix in [
    ('ZombiesAll',{'delveCorruptedWalker':.1}),
    ('ZombiesNight',{'delveCorruptedWalker':.08,'delveImp':.02}),
    ('ZombiesForestDowntown',{'delveCorruptedWalker':.1}),
    ('ZombiesForestDowntownNight',{'delveCorruptedWalker':.08,'delveImp':.02}),
    ('WildGameForestNight',{'delveCrystalStag':.03}),
    ('EnemyAnimalsForest',{'delveThornbackBoar':.08,'delveGloomcat':.02})]:
    name='delveForest_'+source;clone(source,name,mix)
    node(spawning,'set',xpath=f"/spawning/biome[@name='pine_forest']/spawn[@entitygroup='{source}']/@entitygroup").text=name
# Predators belong mainly in Burnt Arbor, and also remain rare in early hordes.
clone('ZombiesBurntForestNight','delveArborNight',{'delveCorruptedWalker':.08,'delveDemonSpawn':.04,'delveImp':.03,'delveHellhound':.025,'delveWarpedBrute':.015,'delvePossessedSoldier':.01})
node(spawning,'set',xpath="/spawning/biome[@name='burnt_forest']/spawn[@entitygroup='ZombiesBurntForestNight']/@entitygroup").text='delveArborNight'

# Every native horde pool has a matching mix. A server-side context selects
# these only for level 1-20 targets or the world's first observed Blood Moon.
# Counts, concurrency, tier caps and native wave schedules remain untouched.
horde_mix={'delveCorruptedWalker':.09,'delveDemonSpawn':.05,'delveImp':.03,'delveHellhound':.014,'delvePossessedSoldier':.01,'delveWarpedBrute':.006}
for source in sorted({s.get('group') for s in E.parse(BASE/'gamestages.xml').findall("./spawner[@name='BloodMoonHorde']/gamestage/spawn")}):
    clone(source,'delveForestHorde_'+source,horde_mix)

# One designated native sleeper volume per authored POI. Preserve all native
# counts, triggers, clear tracking and rally resets; substitute roster slots only.
policies=E.Element('forest')
for file in sorted((release/'Mods/DelveWayrest/Prefabs/POIs').glob('delve_forest_*.xml')):
    if file.stem.endswith('_garden'):continue
    props={p.get('name'):p.get('value') for p in E.parse(file).getroot().findall('property')}
    triples=props['SleeperVolumeGroup'].replace('\n','').split(',')
    counts=[int(triples[i+2]) for i in range(0,len(triples),3)]
    excludes=props.get('SleeperIsQuestExclude','').split(',')
    candidates=[i for i,n in enumerate(counts) if n>=2 and (i>=len(excludes) or excludes[i].lower()!='true')]
    assert candidates,file
    volume=max(candidates,key=lambda i:counts[i])
    kind='soldier' if 'ranger' in file.stem else 'imp' if any(s in file.stem for s in ['cabin_07','cabin_12','cabin_14']) else 'occupation' if 'business' in file.stem else 'corrupted'
    node(policies,'poi',name=file.stem,volume=volume,kind=kind,count=counts[volume])
assert len(policies)==15
# New map variants inherit the exact sleeper metadata from their source POI.
for garden in (release/'Worlds').glob('*/pantry-gardens.xml'):
    for variant in E.parse(garden).getroot():
        source=next(p for p in policies if p.get('name')==variant.get('source'))
        alias=deepcopy(source);alias.set('name',variant.get('target'));policies.append(alias)
save(OUT/'ForestEncounters.xml',policies)
bestiary=E.Element('bestiary')
for e in roster:node(bestiary,'creature',**e)
save(OUT/'Bestiary.xml',bestiary)
for name,root in [('entityclasses',entities),('entitygroups',groups),('spawning',spawning),('items',items),('recipes',recipes),('buffs',buffs)]:save(CFG/(name+'.xml'),root)
with (CFG/'Localization.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','KeepLoaded','english'])
    for key,value in texts.items():w.writerow([key,'ZDelveForest','','','','',value])
save(OUT/'ModInfo.xml',E.fromstring('<xml><Name value="ZDelveForest"/><DisplayName value="Delve Forest Bestiary"/><Version value="0.1.0"/><Author value="Delve"/><Description value="Reusable Forest enemies, magical wildlife and native POI encounter integration."/><SkipWithAntiCheat value="true"/></xml>'))
print(f'Built {len(roster)} enemy definitions, {len(policies)} POI assignments and biome/horde pools.')
