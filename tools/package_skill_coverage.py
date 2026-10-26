"""Package frozen Allium content plus the additive coverage module.

Large immutable assets use hard links to avoid duplicating world/bundle storage.
All editable configuration, launchers, catalogues and evidence are independent.
"""
from pathlib import Path
import json, shutil, os, hashlib, datetime
root=Path(__file__).resolve().parents[1]
base=Path((root/'artifacts/skill-coverage-base.txt').read_text(encoding='utf-8-sig').strip())
assert Path((root/'dist/latest-first-forest-release.txt').read_text(encoding='utf-8-sig').strip())==base,'Latest build changed; reconcile before packaging'
manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8-sig'))
release=root/'dist'/('Delve-Skill-Coverage-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
release.mkdir()
for entry in manifest['files']:
 source=base/entry['path'];target=release/entry['path'];target.parent.mkdir(parents=True,exist_ok=True)
 assert hashlib.sha256(source.read_bytes()).hexdigest().lower()==entry['sha256'].lower(),source
 if source.stat().st_size>1024*1024 and (entry['path'].startswith('Worlds/') or source.suffix.lower() in ('.unity3d','.bundle')):
  os.link(source,target)
 else:shutil.copy2(source,target)
shutil.copytree(root/'src/ZZZZZZZZZDelveSkillCoverage',release/'Mods/ZZZZZZZZZDelveSkillCoverage')
for name in ('START-HERE.txt','SKILL-COVERAGE.txt'):shutil.copy2(root/'docs/skill-coverage-playtest.txt',release/name)
shutil.copytree(root/'artifacts/validation/skill-coverage',release/'Evidence/SkillCoverage')
catalogue_path=release/'Catalogue/first-playtest.json'
catalogue=json.loads(catalogue_path.read_text(encoding='utf-8-sig'))
catalogue['recipes']+=json.loads((root/'artifacts/validation/skill-coverage/recipes.json').read_text())
catalogue['coverage_note']='223 variants; excavation charge at Alchemy 40 is an explicit exception to the existing rank-20 Forest scope.'
catalogue_path.write_text(json.dumps(catalogue,indent=2))
manifest['name']='Allium Existing-Tree Skill Coverage'
manifest['version']='0.10.7-skill-coverage'
manifest['files']=[{'path':p.relative_to(release).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()} for p in sorted(release.rglob('*')) if p.is_file()]
(release/'manifest.json').write_text(json.dumps(manifest,indent=2))
(root/'artifacts/skill-coverage-package.txt').write_text(str(release))
print(release)
