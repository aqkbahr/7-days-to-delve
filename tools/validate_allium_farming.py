"""Validate the pinned farming integration against its shipped Allium baseline."""
from pathlib import Path
from lxml import etree as E
from copy import deepcopy
import json,hashlib,argparse

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,default=ROOT/'playtest/AlliumFarming');args=p.parse_args()
profile=args.profile;mods=profile/'Mods'
sources=json.loads((profile/'integration-sources.json').read_text(encoding='utf-8-sig'))
base=Path(sources['baseRelease']);world=sources['world']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
preserved=0
for old in (base/'Worlds'/world).rglob('*'):
    if old.is_file():
        new=profile/'GeneratedWorlds'/world/old.relative_to(base/'Worlds'/world)
        assert digest(old)==digest(new),('world changed',old);preserved+=1
for mod in (base/'Mods').iterdir():
    if mod.name=='Delve':continue
    old_files={str(f.relative_to(mod)) for f in mod.rglob('*') if f.is_file()}
    new_files={str(f.relative_to(mods/mod.name)) for f in (mods/mod.name).rglob('*') if f.is_file()}
    assert old_files==new_files,('mod file list changed',mod.name)
    for name in old_files:
        assert digest(mod/name)==digest(mods/mod.name/name),(mod.name,name);preserved+=1

native=Path('D:/Steam/steamapps/common/7 Days To Die/Data/Config')
merged={};operations=0
shipping=[m for m in sorted(mods.iterdir()) if m.name!='FarmingProbe' and m.is_dir()]
for mod in shipping:
    for file in (mod/'Config').rglob('*.xml'):
        key=str(file.relative_to(mod/'Config'))
        if key not in merged:merged[key]=E.parse(str(native/key))
        doc=merged[key]
        for op in E.parse(str(file)).getroot():
            if not isinstance(op.tag,str):continue
            targets=doc.xpath(op.get('xpath'));assert targets,(file,op.get('xpath'))
            for target in targets:
                if op.tag=='append':
                    for child in op:target.append(deepcopy(child))
                elif op.tag=='set':
                    assert (op.text or '').strip(),('empty set',file)
                    if getattr(target,'is_attribute',False):target.getparent().set(target.attrname,op.text)
                    else:target.text=op.text
                elif op.tag=='remove':target.getparent().remove(target)
                else:raise AssertionError((file,op.tag))
            operations+=1
for key,tag,attr in [('blocks.xml','block','name'),('items.xml','item','name'),('quests.xml','quest','id'),('entityclasses.xml','entity_class','name'),('entitygroups.xml','entitygroup','name'),('buffs.xml','buff','name')]:
    values=[n.get(attr) for n in merged[key].getroot().findall(tag)]
    assert len(values)==len(set(values)),('duplicate definitions',key)
known={n.get('name') for key,tag in [('blocks.xml','block'),('items.xml','item')] for n in merged[key].getroot().findall(tag)}
# Check every authored recipe after all mods have applied their overrides.
for mod in shipping:
    file=mod/'Config/recipes.xml'
    if not file.exists():continue
    for r in E.parse(str(file)).xpath('//append/recipe'):
        assert r.get('name') in known,('recipe output',r.get('name'))
        for i in r.findall('ingredient'):assert i.get('name') in known,('ingredient',i.get('name'))

# All old core definitions remain. Only the startup inventory is intentionally extended.
parser=E.XMLParser(remove_blank_text=True)
for old in (base/'Mods/Delve/Config').rglob('*.xml'):
    current=mods/'Delve/Config'/old.relative_to(base/'Mods/Delve/Config')
    doc=E.parse(str(current),parser)
    for op in E.parse(str(old),parser).getroot():
        matches=doc.xpath('/configs/*[@xpath=$x]',x=op.get('xpath'))
        assert matches,('lost baseline patch',old,op.get('xpath'))
        if op.tag=='append':
            for child in op:
                if not isinstance(child.tag,str):continue
                key=child.get('name') or child.get('id')
                if key:
                    found=[c for m in matches for c in m if (c.get('name') or c.get('id'))==key]
                    assert any(E.tostring(child)==E.tostring(c) for c in found),('changed baseline definition',old,key)
        elif 'ItemsOnEnterGame' in op.get('xpath',''):
            assert matches[0].text==op.text+',delveFarmHandbook'
        else:assert any(E.tostring(op)==E.tostring(m) for m in matches),('changed baseline patch',old,op.get('xpath'))
out=ROOT/'artifacts/validation/allium-farming';out.mkdir(parents=True,exist_ok=True)
snapshot=[dict(path=str(f.relative_to(mods)).replace('\\','/'),sha256=digest(f)) for m in shipping for f in sorted(m.rglob('*')) if f.is_file()]
(out/'tested-mods.json').write_text(json.dumps(snapshot,indent=2)+'\n')
report=dict(result='PASS',world=world,base_release=base.name,preserved_files=preserved,patch_operations=operations,mods=[m.name for m in shipping])
(out/'content.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
