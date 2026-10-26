"""Complete the queued world/presentation changes on the tested Items Batch 5."""
from pathlib import Path
import shutil,json,csv
from lxml import etree as E
R=Path(__file__).resolve().parents[1];A=R/'artifacts/batch-05-complete';M=R/'src/ZZZZZZZZZZZZDelveBatch05World'
A.mkdir(exist_ok=True)
base=(R/'dist/latest-first-forest-release.txt').read_text(encoding='utf-8-sig').strip()
if not (A/'base.txt').exists():(A/'base.txt').write_text(base)
for p in ['Config/XUi_Menu','Textures','Resources','UIAtlases/ItemIconAtlas']:(M/p).mkdir(parents=True,exist_ok=True)
(M/'ModInfo.xml').write_text('<xml><Name value="DelveBatch05World"/><DisplayName value="Delve Batch 5 - Allium"/><Version value="0.13.1"/><Author value="Delve"/></xml>')
source=Path('C:/Users/Michael/.codex/generated_images/01a16ed9-6290-7943-9a9f-dbcceaba0724')
for dest,id in [('menu','bc105a40-84c3-4337-ad40-4e2c9b1cb1b0'),('wayrest','93b87207-f620-4aa2-b24d-f7dc34c4ed89'),('incursions','f904b6a9-acb3-4f9d-9f2a-be820a4cc4fb')]:shutil.copy2(source/f'exec-{id}.png',M/f'Textures/{dest}.png')
def write(name,root):E.ElementTree(root).write(str(M/'Config'/name),encoding='utf-8',xml_declaration=True,pretty_print=True)
root=E.Element('configs');item=E.SubElement(root,'append',xpath="/items/item[@name='foodDelveBrambleberries']")
# Native item inheritance replaces an authored effect-group list. Verify the
# resulting event in the loaded game; never add three to inherited blueberry two.
g=E.SubElement(item,'effect_group',name='Food Tier 0',tiered='false')
for var in ['$foodAmountAdd','$waterAmountAdd']:E.SubElement(g,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='ModifyCVar',cvar=var,operation='add',value='3')
E.SubElement(g,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='buffProcessConsumables')
E.SubElement(g,'display_value',name='dSmellUse',value='0');write('items.xml',root)
rows=json.loads((R/'artifacts/batch-04/content.json').read_text())['containers'];crates=[r[0] for r in rows if r[1]=='delveIronboundChest']
root=E.Element('configs')
for n in crates:
 for prop,value in [('Model','#@modfolder:Resources/batchfiveworld.unity3d?delveIronboundCrate'),('CustomIcon','delveIronboundCrate')]:E.SubElement(root,'set',xpath=f"/blocks/block[@name='{n}']/property[@name='{prop}']/@value").text=value
write('blocks.xml',root)
(A/'crates.json').write_text(json.dumps(crates,indent=2))
root=E.Element('configs');E.SubElement(root,'remove',xpath="/windows/window[@name='menuBackground']/video")
xp="/windows/window[@name='menuBackground']/texture[@name='bgTexture']"
for key,value in {'texture':'@modfolder:Textures/menu.png','anchor_left':'#cam,0,-5','anchor_right':'#cam,1,5','anchor_bottom':'#cam,0,-5','anchor_top':'#cam,1,5'}.items():E.SubElement(root,'set',xpath=xp+'/@'+key).text=value
# Retain the game's own buttons, logo and loading progress controller.
E.SubElement(root,'set',xpath="/windows/window[@name='loadingScreen']//label[@name='lblTitle']/@color").text='213,184,126'
write('XUi_Menu/windows.xml',root)
root=E.Element('configs');E.SubElement(root,'remove',xpath='/doc/backgrounds/tex');a=E.SubElement(root,'append',xpath='/doc/backgrounds')
for n in ['wayrest','incursions']:E.SubElement(a,'tex',file=f'@modfolder:Textures/{n}.png')
E.SubElement(root,'remove',xpath='/doc/tips/tip');a=E.SubElement(root,'append',xpath='/doc/tips')
for n in ['Wayrest','Incursions']:E.SubElement(a,'tip',key='delveLoading'+n)
write('loadingscreen.xml',root)
labels={'foodDelveBrambleberriesDesc':'Wild brambleberries. Eat raw for 3 food and 3 water, or save them for cooking.','delveLoadingWayrest_title':'WAYREST - A LIGHT IN THE FOREST','delveLoadingWayrest':'Beyond the walls, Allium is dangerous. Wayrest offers a place to gather supplies, learn the crafts and prepare for the road. Visit the steward before venturing farther into the forest.','delveLoadingIncursions_title':"THE QUEEN'S INCURSIONS",'delveLoadingIncursions':"The Queen's incursions threaten even the walls of a refuge. Prepare before nightfall: repair your gear, stock food and remedies, and leave yourself a way to retreat. A strong party brings more than weapons."}
labels.update({n:'Ironbound Supply Crate' for n in crates})
with (M/'Config/Localization.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english']);w.writerows([k,'','',True,False,v] for k,v in labels.items())
print(f'Prepared {M.name}: {len(crates)} container reskins, three backgrounds, berries and lore.')
