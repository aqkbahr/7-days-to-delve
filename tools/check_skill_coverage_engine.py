from pathlib import Path
from lxml import etree as E
import json, hashlib
root=Path(__file__).resolve().parents[1]
profile=root/'playtest/RecipeLearning'
evidence=root/'artifacts/validation/skill-coverage'
cfg=E.parse(str(profile/'serverconfig.xml'))
props={p.get('name'):p.get('value') for p in cfg.getroot()}
dump=profile/'Saves'/props['GameWorld']/props['GameName']/'ConfigsDump'
removed={r['item'] for r in json.loads((evidence/'equipment-audit.json').read_text()) if r['status']=='removed-from-new-supply'}
for kind in ('loot','traders'):
 d=E.parse(str(dump/(kind+'.xml')))
 assert not [n.get('name') for n in d.xpath('//item') if n.get('name') in removed],kind
d=E.parse(str(dump/'quests.xml'))
assert not [n.get('id') for n in d.xpath('//reward') if n.get('id') in removed]
d=E.parse(str(dump/'recipes.xml'))
for r in json.loads((evidence/'recipes.json').read_text()):
 matches=d.xpath('/recipes/recipe[@name=$n]',n=r['name']);assert len(matches)==1,r['name']
 n=matches[0];assert n.get('craft_area')==r['station']
 assert {i.get('name'):int(i.get('count')) for i in n.findall('ingredient')}==r['ingredients']
 assert not n.get('tags','').find('learnable')>=0
package=Path((root/'artifacts/skill-coverage-package.txt').read_text().strip())
hashes=[]
for p in sorted((package/'Mods').rglob('*')):
 if not p.is_file():continue
 relative=p.relative_to(package)
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 assert hashlib.sha256((profile/relative).read_bytes()).hexdigest()==digest,str(relative)
 hashes.append({'path':relative.as_posix(),'sha256':digest})
(evidence/'tested-mods.json').write_text(json.dumps(hashes,indent=2))
result={'result':'PASS','new_recipes':4,'removed_equipment_ids':len(removed),'production_files_match':len(hashes),'base':str(package),'limits':'Native backend/configuration checks; hands-on and multiplayer action attribution pending.'}
(evidence/'engine-merged.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
