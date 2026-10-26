from pathlib import Path
from lxml import etree as E
import json, hashlib, shutil
root=Path(__file__).resolve().parents[1]
evidence=root/'artifacts/validation/skill-coverage'
base=Path((root/'artifacts/skill-coverage-base.txt').read_text(encoding='utf-8-sig').strip())
release=Path((root/'artifacts/skill-coverage-package.txt').read_text().strip())
assert Path((root/'dist/latest-first-forest-release.txt').read_text(encoding='utf-8-sig').strip())==base,'New release appeared; reconcile first'
for name in ('rules.txt','native-recipes.txt','core.txt'):
 text=(evidence/name).read_text(encoding='utf-8-sig');assert 'PASS' in text and 'FAIL' not in text,name
assert json.loads((evidence/'engine-merged.json').read_text())['result']=='PASS'
for row in json.loads((evidence/'tested-mods.json').read_text()):
 assert hashlib.sha256((release/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
log=(root/'playtest/RecipeLearning/server.log').read_text(errors='replace')
bad=[s for s in log.splitlines() if ' EXC ' in s or 'XML loader:' in s or ' ERR XML' in s or 'Exception in thread' in s]
assert not bad,bad
(evidence/'startup.txt').write_text('PASS: latest Batch 04 core and coverage module initialized; no runtime exceptions or XML loader errors.\n')
# Batch 04 changed rune ingredients but inherited an older catalogue. Match its
# frozen recipe fixture and refresh those entries before publishing this build.
fixture=E.parse(str(root/'artifacts/skill-coverage-base-slice.xml'))
catalogue_path=release/'Catalogue/first-playtest.json'
catalogue=json.loads(catalogue_path.read_text(encoding='utf-8-sig'))
cfg=E.parse(str(root/'playtest/RecipeLearning/serverconfig.xml'))
settings={p.get('name'):p.get('value') for p in cfg.getroot()}
dump=root/'playtest/RecipeLearning/Saves'/settings['GameWorld']/settings['GameName']/'ConfigsDump/recipes.xml'
live=E.parse(str(dump))
fixed=0
for row in fixture.getroot():
 key=row.get('key');name,station,count,_=key.split('|')
 if any(r['key']==key for r in catalogue['recipes']):continue
 matches=[r for r in catalogue['recipes'] if r['name'].lower()==name and r.get('station','').lower()==station and str(r['count'])==count]
 assert len(matches)==1,key
 target=matches[0]
 if target['key']==key:continue
 native=[r for r in live.xpath('/recipes/recipe') if r.get('name','').lower()==name and r.get('craft_area','').lower()==station and r.get('count','1')==count]
 assert len(native)==1,key
 target['ingredients']={i.get('name'):int(i.get('count')) for i in native[0].findall('ingredient')}
 computed='|'.join([name,station,count,','.join(sorted(k.lower()+'='+str(v) for k,v in target['ingredients'].items()))])
 assert computed==key,(computed,key)
 target['key']=key;fixed+=1
catalogue_path.write_text(json.dumps(catalogue,indent=2))
(evidence/'catalogue.txt').write_text('PASS: catalogue aligned to 223 tested native recipe signatures; refreshed '+str(fixed)+' inherited Batch 04 ingredient entries.\n')
shutil.copytree(evidence,release/'Evidence/SkillCoverage',dirs_exist_ok=True)
launcher=release/'Play-Allium.ps1'
launcher.write_text(launcher.read_text(encoding='utf-8-sig').replace('Batch 04 installed:','Skill coverage installed:'))
assert (release/'save-data-location.txt').read_bytes()==(base/'save-data-location.txt').read_bytes()
manifest_path=release/'manifest.json'
manifest=json.loads(manifest_path.read_text())
manifest['acceptance']='617 core checks, 223 native recipe variants, 24 coverage rules, engine equipment audit. Hands-on action/UI/multiplayer acceptance pending.'
manifest['files']=[{'path':p.relative_to(release).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sorted(release.rglob('*')) if p.is_file() and p!=manifest_path]
manifest_path.write_text(json.dumps(manifest,indent=2))
print('Finalized candidate '+str(release)+'; run Verify-Package.ps1 before selecting.')
