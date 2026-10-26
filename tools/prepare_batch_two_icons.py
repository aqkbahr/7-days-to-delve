from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1]
audit={x['id'] for x in json.loads((ROOT/'artifacts/batch-02/item-icon-audit.json').read_text())}
icons=[]
for folder,key,bundle in [('ForestWeapons','weapons','forestweapons'),('ForestArmor','armor','forestarmor'),('ForestProps','assets','forestprops')]:
    cat=json.loads((ROOT/f'src/Art/{folder}/catalogue.json').read_text())
    assets={x['id']:x['id'] for x in cat[key]}
    assets.update(cat.get('aliases',{}))
    for name,asset in assets.items():
        if name in audit:icons.append(dict(id=name,asset=asset,bundle=str(ROOT/f'src/ZDelvePresentation/Resources/{bundle}.unity3d')))
project=ROOT/'artifacts/batch-01/art/UnityProject'
shutil.copy2(ROOT/'tools/art/RenderBatchTwoIcons.cs',project/'Assets/Editor/RenderBatchTwoIcons.cs')
(project/'Assets/icon-input.json').write_text(json.dumps(dict(icons=icons,output=str(ROOT/'src/ZZZZDelveBatch02/UIAtlases/ItemIconAtlas')),indent=2))
print(len(icons),'model icons prepared')
