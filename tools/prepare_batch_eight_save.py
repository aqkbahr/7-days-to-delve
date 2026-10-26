from pathlib import Path
import shutil,json,hashlib,zipfile
from lxml import etree as E
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-08';P=R/'playtest/BatchEight';B=Path((A/'base.txt').read_text());data=Path((B/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02';dest=P/'Saves/Allium-v0.10/ForestTest02'
assert not dest.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()};(A/'save-before.json').write_text(json.dumps(files,indent=2))
with zipfile.ZipFile(A/'ForestTest02-before-batch08.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in files:z.write(save/n,'ForestTest02/'+n)
shutil.copytree(save,dest)
cfg=E.parse(str(P/'serverconfig.xml'));cfg.find("property[@name='GameName']").set('value','ForestTest02');cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True)
for p in [R/'tools/prepare_batch_eight.py',A/'furnishings.xml',P/'Mods/StationProbe/furnishings.xml']:
 s=p.read_text();p.write_text(s.replace('cntBookcaseWooden','cntBookcaseFull'))
for mod in [R/'src/ZZZZZZZZZZZZZDelveBatch08',P/'Mods/ZZZZZZZZZZZZZDelveBatch08']:
 shutil.copy2(A/'art/Bundle/fieldmatbatch08.unity3d',mod/'Resources/fieldmatbatch08.unity3d');shutil.copy2(A/'art/Preview/delveFieldCraftingMat.png',mod/'UIAtlases/ItemIconAtlas/delveFieldCraftingMat.png')
print('Copied and backed up ForestTest02; active save untouched')
