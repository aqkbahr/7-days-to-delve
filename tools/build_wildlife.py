"""Double default ambient prey spawn opportunities; retain native caps and presets."""
from pathlib import Path
from decimal import Decimal
import json
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
native=E.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/spawning.xml')
out=ROOT/'src/DelveWildlife';(out/'Config').mkdir(parents=True,exist_ok=True)
patch=E.Element('configs');changes=[]
prey={'WildGameForest','WildGameForestNight','WildGameStagNight'}
for biome in native.getroot().findall('biome'):
    for spawn in biome.findall('spawn'):
        if spawn.get('entitygroup') not in prey:continue
        delays=spawn.get('respawndelay').split(',');old=delays[0]
        delays[0]=str(Decimal(old)/2)
        # Stable biome/spawn IDs also work when another mod substitutes its prey group.
        xpath=f"/spawning/biome[@name='{biome.get('name')}']/spawn[@id='{spawn.get('id')}']/@respawndelay"
        E.SubElement(patch,'set',xpath=xpath).text=','.join(delays)
        changes.append(dict(biome=biome.get('name'),id=spawn.get('id'),group=spawn.get('entitygroup'),
                            old_default_days=old,new_default_days=delays[0],time=spawn.get('time')))
assert len(changes)==9 and len({c['biome'] for c in changes})==5
E.indent(patch);E.ElementTree(patch).write(out/'Config/spawning.xml',encoding='utf-8',xml_declaration=True)
mod=E.fromstring('<xml><Name value="DelveWildlife"/><DisplayName value="Delve - More Prey"/><Description value="Twice as frequent default ambient prey spawn opportunities in all five biomes."/><Author value="Delve"/><Version value="1.0.0"/></xml>')
E.indent(mod);E.ElementTree(mod).write(out/'ModInfo.xml',encoding='utf-8',xml_declaration=True)

# Apply the actual generated XPath patch and ensure no unrelated spawn attributes change.
from lxml import etree
base=etree.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/spawning.xml')
before=etree.tostring(base)
for operation in etree.parse(str(out/'Config/spawning.xml')).getroot():
    targets=base.xpath(operation.get('xpath'));assert len(targets)==1
    attr=targets[0];attr.getparent().set(attr.attrname,operation.text)
original=etree.fromstring(before)
changed=0
for a,b in zip(original.xpath('//spawn'),base.xpath('//spawn')):
    if a.attrib==b.attrib:continue
    assert a.get('entitygroup') in prey
    assert {k:v for k,v in a.attrib.items() if k!='respawndelay'}=={k:v for k,v in b.attrib.items() if k!='respawndelay'}
    av=a.get('respawndelay').split(',');bv=b.get('respawndelay').split(',')
    assert av[1:]==bv[1:] and Decimal(av[0])==Decimal(bv[0])*2
    changed+=1
assert changed==9
evidence=ROOT/'artifacts/validation/wildlife';evidence.mkdir(parents=True,exist_ok=True)
(evidence/'rates.json').write_text(json.dumps(dict(result='PASS',changes=changes,limits='Default animal-respawn setting only; actual animal sightings depend on native population caps, empty selections, time, and loaded terrain.'),indent=2))
print(json.dumps(changes,indent=2))
