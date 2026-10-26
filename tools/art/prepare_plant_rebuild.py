"""Isolated plant art project. Preserve production and all existing asset addresses."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[2]
STAGE=Path('D:/Projects/Codex/7DaysToDelve/PlantRebuild20261026')
for folder in ('Sources','Reports','Review','Delivery/Resources','Delivery/UIAtlases/ItemIconAtlas','Artwork','UnityProject/Assets/Editor','UnityProject/ProjectSettings','UnityProject/Packages'):
    (STAGE/folder).mkdir(parents=True,exist_ok=True)
original=ROOT/'artifacts/forest-props/UnityProject'
assets=STAGE/'UnityProject/Assets'
if not (assets/'Generated').exists():
    shutil.copytree(original/'Assets',assets,dirs_exist_ok=True,ignore=lambda p,ns:[n for n in ns if n=='Editor' or n.endswith('.cs') or n.endswith('.cs.meta')])
for name in ('ProjectVersion.txt','TagManager.asset'):
    if (original/'ProjectSettings'/name).exists():shutil.copy2(original/'ProjectSettings'/name,STAGE/'UnityProject/ProjectSettings'/name)
shutil.copy2(Path(__file__).with_name('plant_unity_packages.json'),STAGE/'UnityProject/Packages/manifest.json')
cat=json.loads((ROOT/'src/Art/ForestProps/catalogue.json').read_text())
extras={'foodDelveBrambleberries','resourceDelveYarrow','resourceDelveThyme','resourceDelveMooncap','delveDriedYarrow','delveDriedThyme'}
specs=[s for s in cat['assets'] if s['kind']=='plant' or s['id'].endswith('1_Seed') or s['id'] in extras]
for s in specs:
    s['source']=str(ROOT/'src/Art/ForestProps'/s['id']/(s['id']+'.blend'))
    assert Path(s['source']).exists(),s['id']
assert len(specs)==26,len(specs)
(STAGE/'plants.json').write_text(json.dumps({'assets':specs,'aliases':cat['aliases']},indent=2))
shutil.copy2(ROOT/'tools/art/PlantRebuild.cs',assets/'Editor/PlantRebuild.cs')
shutil.copy2(ROOT/'tools/art/PlantSurface.shader',assets/'PlantSurface.shader')
atlas=Path('C:/Users/Michael/.codex/generated_images/01a170ad-cf41-71c0-b020-65ba9f6a6896/exec-11cfbe6b-b4ca-417d-ac19-f6d012e29397.png')
shutil.copy2(atlas,STAGE/'Artwork/BotanicalAtlas-original.png')
baseline={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/ZDelvePresentation/Config/blocks.xml',ROOT/'src/ZDelvePresentation/Config/items.xml',ROOT/'src/ZDelvePresentation/Resources/forestprops.unity3d'] if p.exists()}
(STAGE/'Reports/production-baseline.json').write_text(json.dumps(baseline,indent=2))
print('Prepared',len(specs),'plant and botanical item models at',STAGE)
