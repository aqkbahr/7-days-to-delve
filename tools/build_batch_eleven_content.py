from pathlib import Path
from lxml import etree as E
import build_forest_slice as F
import json,csv,copy,shutil
R=Path(__file__).resolve().parents[1];P=R/'playtest/BatchEleven';M=R/'src/ZZZZZZZZZZZZZZZZZDelveBatch11';A=R/'artifacts/batch-11'
F.MOD_NAMES=sorted(p.name for p in (P/'Mods').iterdir() if (p/'ModInfo.xml').exists() and p.name!=M.name)
trees={n:F.merge(P/'Mods',n).getroot() for n in ['items','blocks','recipes','quests','traders','loot','ui_display']}
outputs={n:E.Element('configs') for n in trees};loc=[]
def append(n,x):return E.SubElement(outputs[n],'append',xpath=x)
def setprop(n,name,prop,value):
 node=trees[n].find(f"{n[:-1]}[@name='{name}']");xp=f"/{n}/{n[:-1]}[@name='{name}']"
 if node is not None and node.find(f"property[@name='{prop}']") is not None:E.SubElement(outputs[n],'set',xpath=xp+f"/property[@name='{prop}']/@value").text=value
 else:E.SubElement(append(n,xp),'property',name=prop,value=value)
def label(k,v):loc.append([k,'DelveBatch11','','','',v])
# Sealed shipping crates keep their existing damage/downgrade behavior.
sealed=[]
for b in trees['blocks'].findall('block'):
 if b.get('name','').startswith('cntShippingCrate') and b.find("property[@name='Model']") is not None and 'delveIronboundCrate' in b.find("property[@name='Model']").get('value',''):
  sealed.append(b.get('name'));setprop('blocks',b.get('name'),'Model','#@modfolder:Resources/batcheleven.unity3d?delveSealedIronboundCrate')
# The same soft sound replaces reload events for all handheld magic implements.
for n in ['delveStarterWand','delveForgedWand','delveStarterStaff','delveForgedStaff','delveStarterTotem','delveForgedTotem','delveMendingTotem','delveForgedMendingTotem','delveWardTotem']:
 ac=E.SubElement(append('items',f"/items/item[@name='{n}']"),'property',{'class':'Action0'});E.SubElement(ac,'property',name='Sound_reload',value='delveMagicRechargeWhoosh')
 # Action patches must retain Class so native item loading can resolve them.
 E.SubElement(ac,'property',name='Class',value='Ranged')
sounds=E.Element('configs');sound=E.SubElement(E.SubElement(sounds,'append',xpath='/Sounds'),'SoundDataNode',name='delveMagicRechargeWhoosh')
E.SubElement(sound,'AudioSource',name='@:Sounds/Prefabs/AudioSource_Reloads.prefab');E.SubElement(sound,'AudioClip',ClipName='#@modfolder:Resources/batcheleven.unity3d?delveMagicRechargeWhoosh');E.SubElement(sound,'NoiseScale',value='0.05');E.SubElement(sound,'MaxVoices',value='3')
E.ElementTree(sounds).write(str(M/'Config/sounds.xml'),encoding='utf-8',pretty_print=True)
# Native category lists were missing for our custom station IDs.
stations=sorted({r.get('craft_area') for r in trees['recipes'].findall('recipe') if r.get('craft_area','').startswith('delve')})
cats=[('All','ui_game_symbol_hammer'),('Stations','ui_game_symbol_map_house'),('Weapons','ui_game_symbol_knife'),('Armor','ui_game_symbol_armor_iron'),('Tools','ui_game_symbol_tool'),('Materials','ui_game_symbol_resource'),('Food','ui_game_symbol_fork'),('Alchemy','ui_game_symbol_science'),('Seeds','ui_game_symbol_tree'),('Orders','ui_game_symbol_coin')]
for station in stations:
 if trees['ui_display'].find(f"crafting_category_display/crafting_category_list[@display_type='{station}']") is not None:E.SubElement(outputs['ui_display'],'remove',xpath=f"/ui_display_info/crafting_category_display/crafting_category_list[@display_type='{station}']")
 node=E.SubElement(append('ui_display','/ui_display_info/crafting_category_display'),'crafting_category_list',display_type=station)
 for name,icon in cats:E.SubElement(node,'crafting_category',name='delveCat'+name,icon=icon,display_name='delveCat'+name)
for name,_ in cats:label('delveCat'+name,{'Stations':'Stations / Add-ons','Orders':'Supply Orders'}.get(name,name))
(M/'Config/XUi_InGame').mkdir(exist_ok=True)
(M/'Config/XUi_InGame/windows.xml').write_text('''<configs><set xpath="/windows/window[@name='windowCraftingList']//grid[@name='categories']/@cols">10</set><set xpath="/windows/window[@name='windowCraftingList']//grid[@name='categories']/@cell_width">39</set><set xpath="/windows/window[@name='windowCraftingList']//grid[@name='categories']/@pos">20,-21</set></configs>''')
# Direct farm exchanges. Distinct exact recipe keys retain native queue persistence.
exchanges=[]
orders=[('Pantry','Wayrest Pantry','Farming',1,'casinoCoin',60,[('foodCropCorn',6),('foodCropPotato',4)]),('Herbs','Infirmary: Dried Herbs','Alchemy',10,'casinoCoin',90,[('delveDriedYarrow',3),('delveDriedThyme',2)]),('Bread','Guard: Bread Supply','Cooking',10,'casinoCoin',140,[('foodDelveTravelBread',4)]),('Medicine','Infirmary: Tinctures','Alchemy',20,'casinoCoin',180,[('medicalDelveYarrowTincture',3)]),('Rations','Expedition: Rations','Cooking',20,'casinoCoin',240,[('foodDelveTrailRation',4)]),('Iron','Smithy: Potato Supper','Cooking',1,'resourceForgedIron',4,[('foodBakedPotato',6)]),('Leather','Outfitters: Corn Bread','Cooking',1,'resourceLeather',6,[('foodCornBread',4)])]
def key(r):return r.get('name').lower()+'|'+r.get('craft_area','').lower()+'|'+r.get('count','1')+'|'+','.join(sorted(i.get('name').lower()+'='+i.get('count') for i in r.findall('ingredient')))
for suffix,title,skill,rank,payment,count,ingredients in orders:
 r=E.SubElement(append('recipes','/recipes'),'recipe',name=payment,count=str(count),craft_time='10',craft_area='delveFarmDispatch',tags='delveSupplyExchange')
 for n,c in ingredients:E.SubElement(r,'ingredient',name=n,count=str(c))
 exchanges.append(dict(key=key(r),title='Supply Order: '+title,skill=skill,rank=rank,payment=payment,count=count))
for suffix,*_ in orders[:5]:
 for kind in ['Notice','Parcel']:E.SubElement(outputs['recipes'],'remove',xpath=f"/recipes/recipe[@name='delveFarm{kind}{suffix}']")
 # Old notices stay usable for existing parcels, but no new notices/parcels can be manufactured.
 label('delveFarmNotice'+suffix+'Desc','Legacy supply notice: read to redeem an existing matching sealed parcel. New supply orders pay directly when crafted at the Farm Workbench.')
 label('delveFarmParcel'+suffix+'Desc','Legacy sealed supplies. Redeem with your existing matching supply notice, or exchange this parcel for its original payment at the Farm Workbench.')
 payment=next(o for o in orders if o[0]==suffix)[5]
 r=E.SubElement(append('recipes','/recipes'),'recipe',name='casinoCoin',count=str(payment),craft_time='1',craft_area='delveFarmDispatch',tags='delveSupplyExchange')
 E.SubElement(r,'ingredient',name='delveFarmParcel'+suffix,count='1');exchanges.append(dict(key=key(r),title='Redeem legacy parcel: '+suffix,skill='Farming',rank=1,payment='casinoCoin',count=payment))
# Guaranteed three distinct lesson books for every ordinary NPC trader restock.
books=['delveLesson'+s+'Notes' for s in ['Farming','Cooking','Mining','Smithing','Carpentry','Alchemy']]
g=E.SubElement(append('traders','/traders/trader_item_groups'),'trader_item_group',name='delveLessonRestock11')
for b in books:E.SubElement(g,'item',name=b,count='1')
if trees['traders'].xpath("trader_info/trader_items/item[@group='delveCraftingTomes']"):E.SubElement(outputs['traders'],'remove',xpath="/traders/trader_info/trader_items[item[@group='delveCraftingTomes']]")
traderids=[]
for t in trees['traders'].findall('trader_info'):
 if t.get('is_vending')=='true' or t.get('player_owned')=='true' or t.get('rentable')=='true':continue
 traderids.append(t.get('id'));node=E.SubElement(append('traders',f"/traders/trader_info[@id='{t.get('id')}']"),'trader_items',count='all');E.SubElement(node,'item',group='delveLessonRestock11',count='3',unique_only='true')
# Three distinct reward families, with a small book chance in the equipment slot.
groups={'delveReward11Supplies':[('resourceForgedIron','8'),('resourceLeather','12'),('resourceCloth','20'),('delveCharcoal','15'),('resourceScrapLead','25'),('resourceGlue','5')], 'delveReward11Provisions':[('delveHealingPoultice','3'),('foodCornBread','3'),('foodBakedPotato','5'),('foodDelveCookedBerries','5'),('drinkJarBoiledWater','3'),('medicalBandage','5')], 'delveReward11Gear':[('delveBoneDagger','1'),('delveOakCudgel','1'),('delveAshSpear','1'),('delveBorderBow','1'),('delveWandRune','30'),('delveStaffRune','20'),('delveTotemRune','20'),('delveHealingRune','15')]}
for group,entries in groups.items():
 g=E.SubElement(append('loot','/lootcontainers'),'lootgroup',name=group,count='1')
 for n,c in entries:E.SubElement(g,'item',name=n,count=c,prob='1')
 if group.endswith('Gear'):
  for b in books:E.SubElement(g,'item',name=b,count='1',prob='0.1')
questids=[]
for q in trees['quests'].findall('quest'):
 tier=q.find("property[@name='difficulty_tier']")
 if q.get('id') in ['delveWayrestFetch','delveWayrestClear','delveWayrestFetchClear'] or tier is not None and tier.get('value')=='1' and q.find("reward[@ischosen='true']") is not None:
  questids.append(q.get('id'));xp=f"/quests/quest[@id='{q.get('id')}']";E.SubElement(outputs['quests'],'remove',xpath=xp+"/reward[@ischosen='true']")
  for group in groups:E.SubElement(append('quests',xp),'reward',type='LootItem',id=group,value='1',ischosen='true')
# Keep both world counters in a non-completing journal entry, hidden on HUD.
buffs=E.Element('configs')
for b in ['delveWorldJournal','delveWayrestProgress']:E.SubElement(buffs,'setattribute',xpath=f"/buffs/buff[@name='{b}']",name='hidden').text='true'
E.ElementTree(buffs).write(str(M/'Config/buffs.xml'),encoding='utf-8',pretty_print=True)
q=E.SubElement(append('quests','/quests'),'quest',id='delveWorldProgressJournal11')
for n,v in [('name_key','delveWorldProgressJournal11'),('description_key','delveWorldProgressJournal11Desc'),('category_key','delveQuestCategory'),('repeatable','false'),('shareable','false'),('add_to_tier_complete','false'),('icon','ui_game_symbol_challenge')]:E.SubElement(q,'property',name=n,value=v)
E.SubElement(q,'objective',type='DelveWorldCounters, DelveBatchEleven',value='1',phase='1')
label('delveWorldProgressJournal11','Allium: World Progress');label('delveWorldProgressJournal11Desc','Shared progress across this world. Corrupted enemies defeated and Wayrest contracts are separate counters. This journal remains available as a reference.')
for n,t in outputs.items():E.ElementTree(t).write(str(M/'Config'/f'{n}.xml'),encoding='utf-8',pretty_print=True)
with (M/'Config/Localization.csv').open('w',newline='',encoding='utf-8') as f:w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english']);w.writerows(loc)
code='using System.Collections.Generic; namespace DelveBatchEleven { public class Exchange {public string Title,Skill;public int Rank;public Exchange(string t,string s,int r){Title=t;Skill=s;Rank=r;}} public static class Exchanges {public static readonly Dictionary<string,Exchange> Rows=new Dictionary<string,Exchange>{\n'+',\n'.join('{'+json.dumps(r['key'])+',new Exchange('+json.dumps(r['title'])+','+json.dumps(r['skill'])+','+str(r['rank'])+')}' for r in exchanges)+'};}}'
(M/'Exchanges.generated.cs').write_text(code)
(A/'content.json').write_text(json.dumps(dict(stations=stations,exchanges=exchanges,traders=traderids,quests=questids,books=books,sealed=sealed),indent=2))
shutil.copytree(M,P/'Mods'/M.name,dirs_exist_ok=True)
print(f'{len(stations)} station category lists; {len(exchanges)} direct exchanges; {len(traderids)} trader stock lists; {len(questids)} varied quest rewards')
