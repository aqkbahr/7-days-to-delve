from pathlib import Path
from datetime import datetime
import shutil,json,hashlib,zipfile,uuid,csv
from lxml import etree as E
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-09';P=R/'playtest/BatchNine';B=R/'dist/Delve-Batch08-20261026-124818';M=R/'src/ZZZZZZZZZZZZZZDelveBatch09'
A.mkdir(exist_ok=True);assert not P.exists(),'Do not overwrite a fixture';(A/'base.txt').write_text(str(B))
data=Path((B/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()};(A/'save-before.json').write_text(json.dumps(before,indent=2))
with zipfile.ZipFile(A/'ForestTest02-before-batch09.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in before:z.write(save/n,'ForestTest02/'+n)
shutil.copytree(save,P/'Saves/Allium-v0.10/ForestTest02')
for e in json.loads((B/'manifest.json').read_text())['files']:
 n=e['path']
 if n.startswith(('Mods/','Worlds/')):
  dest=P/n.replace('Worlds/','GeneratedWorlds/',1);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/n,dest)
shutil.copytree(R/'playtest/BatchEight/Mods/StationProbe',P/'Mods/StationProbe')
(M/'Config').mkdir(parents=True,exist_ok=True)
(M/'ModInfo.xml').write_text('<xml><Name value="DelveBatch09"/><DisplayName value="Delve Batch 9 - Recovery and Foraging"/><Version value="0.15.0"/><Author value="Delve"/></xml>')
doc=E.Element('configs')
for n,amount in [('foodDelveBrambleberries',2),('foodDelveCookedBerries',5)]:
 # Replace only the nutrition group. Cooked berries keep their stamina-meal buff.
 xp=f"/items/item[@name='{n}']/effect_group[triggered_effect[@cvar='$foodAmountAdd']]"
 E.SubElement(doc,'remove',xpath=xp)
 group=E.SubElement(E.SubElement(doc,'append',xpath=f"/items/item[@name='{n}']"),'effect_group',tiered='false',name='Delve Berry Nutrition')
 for var in ['$foodAmountAdd','$waterAmountAdd']:E.SubElement(group,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='ModifyCVar',cvar=var,operation='add',value=str(amount))
 E.SubElement(group,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='buffProcessConsumables')
 E.SubElement(group,'display_value',name='dHealth',value='0')
E.ElementTree(doc).write(str(M/'Config/items.xml'),encoding='utf-8',pretty_print=True)
with (M/'Config/Localization.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english']);w.writerow(['foodDelveBrambleberriesDesc','','','','','Wild brambleberries. Eat raw for 2 food and 2 water. Provides no health.']);w.writerow(['foodDelveCookedBerriesDesc','','','','','Cooked berries. Restores 5 food and 5 water, with no health restoration. Grants the existing Forest Meal stamina bonus.'])
shutil.copytree(M,P/'Mods'/M.name)
cfg=E.parse(str(R/'playtest/BatchEight/serverconfig.xml'))
for n,v in {'UserDataFolder':str(P),'GameName':'ForestTest02','ServerName':'Batch Nine Recovery Verification','ServerPort':'29510','TelnetPort':'29519','TelnetPassword':uuid.uuid4().hex}.items():cfg.find(f"property[@name='{n}']").set('value',v)
cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True);(P/'profile.json').write_text(json.dumps({'GamePath':'D:/Steam/steamapps/common/7 Days To Die','ProfilePath':str(P)}))
# Preserve the exact failed compressed/uncompressed payloads for native recovery.
shutil.copytree(save/'Region',A/'original-regions')
(A/'game-api-sha256.txt').write_text(sha(Path('D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed/Assembly-CSharp.dll')))
print('Backed up current save and prepared isolated 3.4 recovery fixture on D:')
