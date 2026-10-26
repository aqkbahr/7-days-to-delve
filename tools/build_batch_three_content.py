from pathlib import Path
import xml.etree.ElementTree as E, shutil,csv
r=Path.cwd(); mod=r/'src/ZZZZZZDelveBatch03'; (mod/'Config').mkdir(parents=True,exist_ok=True);(mod/'Resources').mkdir(exist_ok=True);(mod/'UIAtlases/ItemIconAtlas').mkdir(parents=True,exist_ok=True)
(mod/'ModInfo.xml').write_text('<xml><Name value="ZZZZZZDelveBatch03"/><DisplayName value="Delve Playtest Batch 3"/><Version value="0.10.5"/><Author value="Delve"/></xml>')
blocks=E.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/blocks.xml').getroot();carts=[b.get('name') for b in blocks if b.get('name','').startswith('cntShoppingCart')];root=E.Element('configs')
for name in carts:
 xp=f"/blocks/block[@name='{name}']";scattered='Tipped' in name;model='delveCrateStackScattered' if scattered else 'delveCrateStack'
 for key,value in {'Model':f'#@modfolder:Resources/batchthree.unity3d?{model}','CustomIcon':model,'TintColor':'FFFFFF','CustomIconTint':'FFFFFF','Class':'CompositeTileEntity','Shape':'ModelEntity'}.items():
  original=blocks.find(f"block[@name='{name}']")
  if original.find(f"property[@name='{key}']") is not None:E.SubElement(root,'remove',xpath=xp+f"/property[@name='{key}']")
  append=E.SubElement(root,'append',xpath=xp);E.SubElement(append,'property',name=key,value=value)
 if blocks.find(f"block[@name='{name}']/property[@class='CompositeFeatures']") is not None:E.SubElement(root,'remove',xpath=xp+"/property[@class='CompositeFeatures']")
 if blocks.find(f"block[@name='{name}']/property[@name='DowngradeBlock']") is not None:E.SubElement(root,'remove',xpath=xp+"/property[@name='DowngradeBlock']")
 a=E.SubElement(root,'append',xpath=xp);f=E.SubElement(a,'property',{'class':'CompositeFeatures'});st=E.SubElement(f,'property',{'class':'TEFeatureStorage'});E.SubElement(st,'property',name='LootList',value='shoppingCart')
E.indent(root);E.ElementTree(root).write(mod/'Config/blocks.xml',encoding='utf-8',xml_declaration=True)
with (mod/'Config/Localization.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english']);w.writerows((n,'blocks','','','','Scattered Supply Crates' if 'Tipped' in n else 'Stacked Supply Crates') for n in carts)
shutil.copy2(r/'artifacts/batch-03/art/Bundle/batchthree.unity3d',mod/'Resources')
for n in ('delveCrateStack','delveCrateStackScattered'):shutil.copy2(r/f'artifacts/batch-03/art/Preview/{n}.png',mod/'UIAtlases/ItemIconAtlas')
shutil.copytree(mod,r/'artifacts/batch-03/candidate/Mods'/mod.name,dirs_exist_ok=True)
print('Authored',len(carts),'crate replacements; no storage-reset downgrade')
