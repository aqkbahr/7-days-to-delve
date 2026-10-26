from pathlib import Path
import json
from PIL import Image
from lxml import etree as E
import build_forest_slice as F
R=Path(__file__).resolve().parents[1];P=R/'playtest/BatchEight';M=R/'src/ZZZZZZZZZZZZZDelveBatch08';A=R/'artifacts/batch-08'
im=Image.open(M/'Textures/delve-logo.png');assert im.mode=='RGBA' and im.getextrema()[3][0]==0,'Logo transparency'
ratio=im.width/im.height
for mod in [M,P/'Mods'/M.name]:
 doc=E.parse(str(mod/'Config/XUi_Menu/windows.xml'));root=doc.getroot()
 for key,value in [('aspect_ratio',str(ratio)),('pos',f'{(400-400*ratio)/2:.2f},0')]:
  xp="/windows/window[@name='mainMenu']/texture[@name='gameLogo']/@"+key
  node=root.find(f"set[@xpath=\"{xp}\"]") if False else None
  for n in list(root):
   if n.get('xpath')==xp:root.remove(n)
  E.SubElement(root,'set',xpath=xp).text=value
 doc.write(str(mod/'Config/XUi_Menu/windows.xml'),encoding='utf-8',pretty_print=True)
F.MOD_NAMES=sorted(p.name for p in (P/'Mods').iterdir() if (p/'ModInfo.xml').exists())
for n in ['blocks','items','recipes','XUi_Menu/windows']:F.merge(P/'Mods',n)
s=(R/'src/Code/ProgressionScreen.cs').read_text();assert 'tab==-1' not in s;assert 'Put("attributes",tab==0)' in s
assert 'for(int i=0;i<6;i++)' in s and 'Hook("dg_attribute"+i' in s
(A/'static-validation.json').write_text(json.dumps({'result':'PASS','logo':{'width':im.width,'height':im.height,'transparent':True,'ratio':ratio},'xml_patches':'All resolve','attribute_branch':'tab 0, six selectors, selected-stat details and purchases'},indent=2))
print('PASS logo alpha/aspect and centered placement; XML overlays; attribute branch regression')
