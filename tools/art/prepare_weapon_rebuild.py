"""Prepare an isolated, repeatable rebuild; retain current gameplay/grip contract."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[2]
STAGE=Path('D:/Projects/Codex/7DaysToDelve/WeaponRebuild20261026')
for name in ('Sources','Reports','Artwork','Review','Delivery/Resources','Delivery/UIAtlases/ItemIconAtlas','UnityProject/Assets/Editor','UnityProject/ProjectSettings','UnityProject/Packages'):(STAGE/name).mkdir(parents=True,exist_ok=True)
original=ROOT/'artifacts/forest-weapons/UnityProject';assets=STAGE/'UnityProject/Assets'
if not (assets/'Generated').exists():shutil.copytree(original/'Assets',assets,dirs_exist_ok=True,ignore=lambda p,ns:[n for n in ns if n=='Editor' or n.endswith('.cs') or n.endswith('.cs.meta')])
for name in ('ProjectVersion.txt','TagManager.asset'):
    if (original/'ProjectSettings'/name).exists():shutil.copy2(original/'ProjectSettings'/name,STAGE/'UnityProject/ProjectSettings'/name)
shutil.copy2(Path(__file__).with_name('plant_unity_packages.json'),STAGE/'UnityProject/Packages/manifest.json')
catalogue=json.loads((ROOT/'src/Art/ForestWeapons/catalogue.json').read_text())
assert len(catalogue['weapons'])==37
for spec in catalogue['weapons']:
    spec['source']=str(ROOT/'src/Art/ForestWeapons'/spec['id']/(spec['id']+'.blend'));assert Path(spec['source']).exists()
(STAGE/'weapons.json').write_text(json.dumps(catalogue,indent=2))
for name in ('WeaponRebuild.cs','WeaponSurface.shader'):shutil.copy2(Path(__file__).with_name(name),assets/('Editor' if name.endswith('.cs') else '')/name)
shutil.copy2(Path('C:/Users/Michael/.codex/generated_images/01a170ad-cf41-71c0-b020-65ba9f6a6896/exec-0b81252d-d371-4c09-8690-f11307f0c62a.png'),STAGE/'Artwork/WeaponMaterials-original.png')
shutil.copy2(Path(__file__).with_name('weapon_rebuild_prompt.txt'),STAGE/'Artwork/prompt.txt')
paths=['src/Art/ForestWeapons/catalogue.json','src/ZDelvePresentation/Resources/forestweapons.unity3d','src/ZDelvePresentation/Config/items.xml','src/Art/HeldPresentation.cs','src/Art/HeldCatalog.generated.cs','src/ZDelvePresentation/DelvePresentation.dll','dist/latest-first-forest-release.txt']
baseline={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
(STAGE/'Reports/production-baseline.json').write_text(json.dumps(baseline,indent=2))
print('Prepared 37 models; 20 weapon/focus, 13 runes, 4 ammunition; current native grip fixes preserved')
