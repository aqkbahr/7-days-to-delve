from pathlib import Path
from lxml import etree as E
import json,re,copy,csv,shutil
import build_forest_slice as F
R=Path(__file__).resolve().parents[1];P=R/'playtest/BatchTen';M=R/'src/ZZZZZZZZZZZZZZZDelveBatch10';A=R/'artifacts/batch-10'
F.MOD_NAMES=sorted(p.name for p in (P/'Mods').iterdir() if (p/'ModInfo.xml').exists() and p.name!=M.name)
recipes=F.merge(P/'Mods','recipes');blocks=F.merge(P/'Mods','blocks');items=F.merge(P/'Mods','items')
out=E.Element('configs');rows=[]
def key(r):return r.get('name').lower()+'|'+r.get('craft_area','').lower()+'|'+r.get('count','1')+'|'+','.join(sorted(i.get('name').lower()+'='+i.get('count') for i in r.findall('ingredient')))
def moved(r,areas,skill,rank):
 xp="/recipes/recipe[@name='%s' and not(@craft_area)]"%r.get('name');E.SubElement(out,'remove',xpath=xp)
 for area in areas:
  n=copy.deepcopy(r);n.set('craft_area',area);E.SubElement(out,'append',xpath='/recipes').append(n);rows.append(dict(key=key(n),name=n.get('name'),station=area,skill=skill,rank=rank))
for name in ['delveWandRune','delveStaffRune','delveTotemRune','delveHealingRune']:
 r=recipes.xpath(f"/recipes/recipe[@name='{name}' and not(@craft_area)]");assert len(r)==1
 moved(r[0],['delveFieldCraftingMat','delveInscriptionKit'],'Alchemy',1)
basic={'Farming':'delveSawKit','Cooking':'delveMortarKit','Smithing':'delveForgeAnvil','Carpentry':'delveSawKit','Alchemy':'delveMortarKit','Mining':'delveForgeAnvil'}
advanced={'delveUpgradeSeedPress':'delveSawKit','toolCookingGrill':'delveForgeAnvil','delveUpgradePreservingCrock':'delveMortarKit','delveUpgradeBellows':'delveOutfittingKit','delveUpgradePrecisionJig':'delveSawKit','delveUpgradeArmorForm':'delveSawKit','delveUpgradeFermenter':'delveSawKit','delveUpgradeEtchingTools':'delveForgeAnvil','delveUpgradeOreSieve':'delveSawKit','toolDewFilter':'delveMortarKit'}
catalog=(R/'src/StationUpgrades/Catalog.generated.cs').read_text()
for oldkey,name,skill,rank in re.findall(r'case "([^"]+)":return new Row\("([^"]+)","([^"]+)",(\d+)\);',catalog):
 if '|' not in oldkey or not (name.startswith('delveUpgrade') or name in ['toolCookingPot','toolCookingGrill','toolDewGatherer','toolDewTarp','toolDewFilter']):continue
 rank=int(rank);r=recipes.xpath(f"/recipes/recipe[@name='{name}' and not(@craft_area)]");assert len(r)==1,name
 station=advanced[name] if rank==20 else ('delveForgeAnvil' if name in ['toolCookingPot','delveUpgradeEngravingTools'] else basic[skill])
 if name=='toolCookingPot':station='delveFieldHearth'
 moved(r[0],(['delveFieldCraftingMat',station] if rank==10 else [station]),skill,rank)
# A basic forged farming tool. Higher quality uses the standard crafting quality UI.
r=E.SubElement(E.SubElement(out,'append',xpath='/recipes'),'recipe',name='delveHarvestScythe',count='1',craft_time='30',craft_area='delveForgeAnvil')
for n,c in [('resourceForgedIron',6),('resourceWood',12),('resourceLeather',2)]:E.SubElement(r,'ingredient',name=n,count=str(c))
rows.append(dict(key=key(r),name='delveHarvestScythe',station='delveForgeAnvil',skill='Farming',rank=1))
E.ElementTree(out).write(str(M/'Config/recipes.xml'),encoding='utf-8',pretty_print=True)
b=E.Element('configs');crate_names=[]
for node in blocks.xpath('/blocks/block[property[@name="Model" and contains(@value,"delveIronboundCrate")]]'):
 name=node.get('name');crate_names.append(name);xp=f"/blocks/block[@name='{name}']"
 if node.find("property[@name='ModelOffset']") is not None:E.SubElement(b,'set',xpath=xp+"/property[@name='ModelOffset']/@value").text='0,0,0'
 else:E.SubElement(E.SubElement(b,'append',xpath=xp),'property',name='ModelOffset',value='0,0,0')
E.ElementTree(b).write(str(M/'Config/blocks.xml'),encoding='utf-8',pretty_print=True)
i=E.Element('configs');ap=E.SubElement(i,'append',xpath="/items/item[@name='foodDelveCookedBerries']");ac=E.SubElement(ap,'property',{'class':'Action0'});E.SubElement(ac,'property',name='Create_item',value='')
E.SubElement(ac,'property',name='Class',value='Eat');E.SubElement(ac,'property',name='Delay',value='1.0');E.SubElement(ac,'property',name='Sound_start',value='player_eating');E.SubElement(ac,'property',name='Create_item_count',value='0');E.SubElement(ac,'property',name='Use_jar_refund',value='false')
# Match the wand's native grip/animation rig, while retaining each item's stats.
wand=items.find("item[@name='delveStarterWand']")
for name in ['delveStarterStaff','delveForgedStaff','delveStarterTotem','delveForgedTotem','delveMendingTotem','delveForgedMendingTotem','delveWardTotem']:
 node=items.find(f"item[@name='{name}']")
 for prop in ['Meshfile','HoldType']:
  source=wand.find(f"property[@name='{prop}']")
  if source is None:continue
  xp=f"/items/item[@name='{name}']"
  if node.find(f"property[@name='{prop}']") is not None:E.SubElement(i,'set',xpath=xp+f"/property[@name='{prop}']/@value").text=source.get('value')
  else:E.SubElement(i,'append',xpath=xp).append(copy.deepcopy(source))
sc=E.SubElement(E.SubElement(i,'append',xpath='/items'),'item',name='delveHarvestScythe')
for n,v in {'Extends':'meleeWpnBladeT3Machete','CustomIcon':'delveHarvestScythe','DescriptionKey':'delveHarvestScytheDesc','UnlockedBy':'','CreativeMode':'Player','Tags':'melee,tool,harvestingTool,delveScythe','RepairTools':'resourceForgedIron','EconomicValue':'120','DropMeshfile':'#@modfolder:Resources/batchten.unity3d?delveHarvestScythe'}.items():E.SubElement(sc,'property',name=n,value=v)
eg=E.SubElement(sc,'effect_group',name='Delve farming scythe',tiered='false')
for n,v in [('EntityDamage','5'),('BlockDamage','100'),('StaminaLoss','10'),('AttacksPerMinute','50'),('MaxRange','2.5'),('DegradationPerUse','1')]:E.SubElement(eg,'passive_effect',name=n,operation='base_set',value=v)
E.SubElement(eg,'passive_effect',name='DegradationMax',operation='base_set',value='200,600',tier='1,6')
E.ElementTree(i).write(str(M/'Config/items.xml'),encoding='utf-8',pretty_print=True)
with (M/'Config/Localization.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english']);w.writerow(['delveHarvestScythe','','','','','Harvest Scythe']);w.writerow(['delveHarvestScytheDesc','','','','','Sweep through ripe plants and grass in a three-block-wide forward arc. Quality 1-6 adds 0/10/20/30/40/50 percent harvest yield, excluding seeds. Leaves immature crops, trees and structures intact. Craft at a basic forge.']);w.writerow(['delveUpgradeEngravingToolsDesc','','','','','Alchemy 10. Craft at the Field Crafting Mat or forge, then install in the Rune Bench for efficient batches of basic runes.']);w.writerow(['delveUpgradeEtchingToolsDesc','','','','','Alchemy 20. Craft at the forge, then install in the Rune Bench for Mooncap and etched rune recipes.'])
(A/'recipe-routing.json').write_text(json.dumps(rows,indent=2));(A/'crate-blocks.json').write_text(json.dumps(crate_names))
checks=E.parse(str(R/'playtest/BatchNine/Mods/StationProbe/addon-checks.xml'))
moved_names={r['name'].lower() for r in rows}
for node in list(checks.getroot()):
 if node.tag=='recipe' and node.get('key','').split('|')[0] in moved_names and node.get('key','').split('|')[1]=='':checks.getroot().remove(node)
for row in rows:E.SubElement(checks.getroot(),'recipe',key=row['key'],skill=row['skill'],rank=str(row['rank']),tool='',queue='false')
checks.write(str(P/'Mods/StationProbe/addon-checks.xml'),encoding='utf-8',pretty_print=True)
doc=E.Element('batch')
for row in rows:E.SubElement(doc,'route',**{k:str(v) for k,v in row.items()})
for name in crate_names:E.SubElement(doc,'crate',name=name)
E.ElementTree(doc).write(str(P/'Mods/StationProbe/batch10.xml'),encoding='utf-8',pretty_print=True)
code='using System.Collections.Generic; namespace DelveBatchTen { public class Row {public string Skill;public int Rank;public Row(string s,int r){Skill=s;Rank=r;}} public static class Routes {public static readonly Dictionary<string,Row> Recipes=new Dictionary<string,Row>{\n'
code+=',\n'.join('{"'+r['key']+'",new Row("'+r['skill']+'",'+str(r['rank'])+')}' for r in rows)+'};}}'
(M/'Routes.generated.cs').write_text(code)
shutil.copytree(M,P/'Mods'/M.name,dirs_exist_ok=True);print(f'Created {len(rows)} station-only recipe variants; aligned {len(crate_names)} crate states')


