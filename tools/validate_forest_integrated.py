"""Validate the frozen combined profile, not the moving development core."""
from pathlib import Path
from copy import deepcopy
from lxml import etree as E
import json, hashlib, argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--profile',default='ForestIntegrated');parser.add_argument('--baseline');parser.add_argument('--core-baseline');parser.add_argument('--visibility-fix');parser.add_argument('--evidence',default='forest-integrated');args=parser.parse_args()
PROFILE=ROOT/'playtest'/args.profile; MODS=PROFILE/'Mods'
BASE=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
mods=[p for p in sorted(MODS.iterdir()) if p.is_dir() and p.name not in ('ForestProbe','AlliumTools','HealingProbe','FarmingProbe','TerrainDiagnostic')]
baseline=Path(args.baseline) if args.baseline else Path((ROOT/'artifacts/forest-integrated-base.txt').read_text(encoding='utf-8-sig').strip())
world_name=(baseline/'world-name.txt').read_text(encoding='utf-8-sig').strip()
for mod in mods:
    if mod.name=='ZDelveForest':continue
    expected=(Path(args.core_baseline) if args.core_baseline and mod.name in ('Delve','DelveWildlife') else baseline)/'Mods'/mod.name
    source={str(f.relative_to(expected)):hashlib.sha256(f.read_bytes()).hexdigest() for f in expected.rglob('*') if f.is_file()}
    if args.visibility_fix and mod.name=='Delve':source['DelveSpellVisibility.dll']=hashlib.sha256(Path(args.visibility_fix).read_bytes()).hexdigest()
    actual={str(f.relative_to(mod)):hashlib.sha256(f.read_bytes()).hexdigest() for f in mod.rglob('*') if f.is_file()}
    assert source==actual,('baseline mismatch',mod.name)
expected_world=baseline/'Worlds'/world_name
for file in expected_world.rglob('*'):
    if file.is_file():assert file.read_bytes()==(PROFILE/'GeneratedWorlds'/world_name/file.relative_to(expected_world)).read_bytes(),('world changed',file)
merged={};ops=0
for mod in mods:
    for file in sorted((mod/'Config').rglob('*.xml')):
        key=str(file.relative_to(mod/'Config'))
        if key not in merged:merged[key]=E.parse(str(BASE/key))
        doc=merged[key]
        for op in E.parse(str(file)).getroot():
            if not isinstance(op.tag,str):continue
            targets=doc.xpath(op.get('xpath'));assert targets,(file,op.get('xpath'))
            for target in targets:
                if op.tag=='append':
                    for child in op:target.append(deepcopy(child))
                elif op.tag=='set':
                    if getattr(target,'is_attribute',False):target.getparent().set(target.attrname,op.text or '')
                    else:target.text=op.text or ''
                elif op.tag=='remove':target.getparent().remove(target)
                elif op.tag in ('insertBefore','insertAfter'):
                    for child in op:
                        (target.addprevious if op.tag=='insertBefore' else target.addnext)(deepcopy(child))
                else:raise AssertionError((file,op.tag))
            ops+=1
for key,tag,attr in [('entityclasses.xml','entity_class','name'),('entitygroups.xml','entitygroup','name'),('items.xml','item','name'),('blocks.xml','block','name'),('buffs.xml','buff','name'),('quests.xml','quest','id')]:
    names=[n.get(attr) for n in merged[key].getroot().findall(tag)]
    assert len(names)==len(set(names)),('duplicate',key)
entities={n.get('name'):n for n in merged['entityclasses.xml'].getroot().findall('entity_class')}
items={n.get('name'):n for n in merged['items.xml'].getroot().findall('item')}
groups={n.get('name'):n for n in merged['entitygroups.xml'].getroot().findall('entitygroup')}
roster=json.loads((ROOT/'src/Forest/roster.json').read_text())
for row in roster:
    e=entities[row['id']];assert e.get('extends')==row['parent']
    assert e.find("property[@name='HandItem']").get('value') in items
    assert float(e.find("effect_group/passive_effect[@name='HealthMax']").get('value'))==row['hp']
    for drop in e.findall('drop'):assert drop.get('name') in items
native=E.parse(str(BASE/'gamestages.xml'))
stagegroups={s.get('group') for s in native.xpath("/gamestages/spawner[@name='BloodMoonHorde']/gamestage/spawn")}
for source in stagegroups:
    g=groups['delveForestHorde_'+source]
    assert abs(sum(float(n.get('p','1')) for n in g)-1)<1e-6
    assert abs(sum(float(n.get('p','1')) for n in g if n.get('n').startswith('delve'))-.2)<1e-6
    for e in g:assert e.get('n') in entities and e.get('n') not in ['delveThornbackBoar','delveGloomcat','delveCrystalStag']
# Native horde budgets and schedules are identical, only core's earlier group aliases differ.
for before,after in zip(native.xpath("//spawner[@name='BloodMoonHorde']/gamestage/spawn"),merged['gamestages.xml'].xpath("//spawner[@name='BloodMoonHorde']/gamestage/spawn")):
    assert {k:v for k,v in before.attrib.items() if k!='group'}=={k:v for k,v in after.attrib.items() if k!='group'}
policies={p.get('name'):p for p in E.parse(str(MODS/'ZDelveForest/ForestEncounters.xml')).getroot()}
world=PROFILE/'GeneratedWorlds'/world_name
locations=[]
for decoration in E.parse(str(world/'prefabs.xml')).getroot():
    name=decoration.get('name','')
    if not name.startswith('delve_forest_'):continue
    assert name in policies,('missing mapped POI',name)
    prefab=E.parse(str(MODS/'DelveWayrest/Prefabs/POIs'/(name+'.xml')))
    props={p.get('name'):p.get('value') for p in prefab.getroot().findall('property')}
    groupspec=props['SleeperVolumeGroup'].replace('\n','').split(',')
    policy=policies[name];assert int(groupspec[int(policy.get('volume'))*3+2])>=2
    position=[int(v) for v in decoration.get('position').split(',')]
    size=[int(v) for v in props['PrefabSize'].split(',')]
    # Use a safe point inside the rotated footprint.
    locations.append(dict(name=name,x=position[0]+5,z=position[2]+5,kind=policy.get('kind')))
assert len(locations)==15
spawns=merged['spawning.xml']
old=E.parse(str(BASE/'spawning.xml'))
changed_delay=0
for b in old.getroot().findall('biome'):
    for s in b.findall('spawn'):
        t=spawns.xpath('/spawning/biome[@name=$b]/spawn[@id=$s]',b=b.get('name'),s=s.get('id'))[0]
        assert {k:v for k,v in s.attrib.items() if k not in ('entitygroup','respawndelay')}=={k:v for k,v in t.attrib.items() if k not in ('entitygroup','respawndelay')}
        if s.get('respawndelay')!=t.get('respawndelay'):
            a=s.get('respawndelay').split(',');c=t.get('respawndelay').split(',')
            assert float(a[0])==2*float(c[0]) and a[1:]==c[1:];changed_delay+=1
        assert t.get('entitygroup') in groups
assert changed_delay==9
out=ROOT/'artifacts/validation'/args.evidence;out.mkdir(parents=True,exist_ok=True)
(out/'locations.json').write_text(json.dumps(locations,indent=2))
snapshot=[dict(path=str(f.relative_to(MODS)).replace('\\','/'),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for m in mods for f in sorted(m.rglob('*')) if f.is_file()]
(out/'tested-mods.json').write_text(json.dumps(snapshot,indent=2))
report=dict(result='PASS',patch_operations=ops,creatures=len(roster),placed_pois=len(locations),horde_pools=len(stagegroups),wildlife_delay_changes=changed_delay,mods=[m.name for m in mods])
(out/'content.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
