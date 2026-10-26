from pathlib import Path
import json,copy,csv,shutil,os,uuid,hashlib,zipfile,sys
from lxml import etree as E
sys.path.insert(0,str(Path(__file__).parent))
from build_station_progression import merge
R=Path(__file__).resolve().parents[1];A=R/'artifacts/summoning-20';P=R/'playtest/Summoning20';M=R/'src/ZZZZZZZZZZZZZZZZZZDelveSummoning20'
B=Path((A/'base.txt').read_text()) if (A/'base.txt').exists() else Path(json.loads((R/'dist/active-playtest-release.json').read_text())['release'])
(A/'base.txt').write_text(str(B));(M/'Config/XUi_InGame').mkdir(parents=True,exist_ok=True)
(M/'ModInfo.xml').write_text('<xml><Name value="DelveSummoning20"/><DisplayName value="Delve - Summoning through rank 20"/><Version value="0.18.0"/><Author value="Delve"/></xml>')
def write(name,root):E.ElementTree(root).write(str(M/'Config'/name),encoding='utf-8',pretty_print=True,xml_declaration=True)
items=merge(B,'items');root=E.Element('configs');app=E.SubElement(root,'append',xpath='/items')
rod=copy.deepcopy(items.find("item[@name='delveSummoningRod']"));rod.set('name','delveForgedSummoningRod');app.append(rod)
for name,value in [('DescriptionKey','delveForgedSummoningRodDesc'),('CustomIcon','delveForgedMendingTotem'),('DropMeshfile','#@modfolder(ZDelvePresentation):Resources/forestweapons.unity3d?delveForgedMendingTotem_Drop')]:rod.find(f"property[@name='{name}']").set('value',value)
rod.find("effect_group/passive_effect[@name='DegradationMax']").set('value','400');write('items.xml',root)
recipes=merge(B,'recipes');root=E.Element('configs');app=E.SubElement(root,'append',xpath='/recipes')
recipe=copy.deepcopy(recipes.find("recipe[@name='delveForgedMendingTotem']"));assert recipe.get('craft_area')=='delveSawKitTier3';recipe.set('name','delveForgedSummoningRod');app.append(recipe);write('recipes.xml',root)
names=['BindingDiscipline','PrimalBond','FierceCompanion','StalwartCompanion','EnduringPact'];titles=['Binding Discipline','Primal Bond','Fierce Companion','Stalwart Companion','Enduring Pact']
descs=['+10% summoning rod reload speed.','New summons have 15% more maximum health.','New summons deal 20% more damage.','New summons take 15% less incoming damage from hostile creatures.','New summons last 75 seconds instead of 60. One summon per caster remains the limit.']
root=E.Element('configs');skills=E.SubElement(root,'append',xpath='/progression/skills');E.SubElement(skills,'skill',name='delveTreeSummoning',parent='delveAttWisdom',name_key='delveTreeSummoning',icon='ui_game_symbol_tracking_pig')
perks=E.SubElement(root,'append',xpath='/progression/perks')
for i,name in enumerate(names):
 key='delvePerkSummoning'+name
 p=E.SubElement(perks,'perk',name=key,parent='delveTreeSummoning',name_key=key,desc_key=key+'Desc',icon='ui_game_symbol_tracking_pig',max_level='1',override_cost='1')
 req=E.SubElement(p,'level_requirements',level='1');E.SubElement(req,'requirement',name='CVarCompare',cvar='delveLevelSummoning',operation='GTE',value=str(10 if i<2 else 20),desc_key=key+'Rank')
 if i>=2:
  for prior in names[:2]:E.SubElement(req,'requirement',name='ProgressionLevel',progression_name='delvePerkSummoning'+prior,operation='GTE',value='1',desc_key='delveSummoningFundamentalsRequired')
 eg=E.SubElement(p,'effect_group')
 if i==0:E.SubElement(eg,'passive_effect',name='ReloadSpeedMultiplier',operation='perc_add',value='.1',level='1',tags='delveSummoning')
 E.SubElement(eg,'effect_description',level='1',desc_key=key,long_desc_key=key+'Desc')
write('progression.xml',root)
# Replace only controls whose visibility differs for the five-node early tree.
source=E.parse(str(R/'src/Delve/Config/XUi_InGame/windows.xml'));root=E.Element('configs')
for node in source.xpath("//rect[@name='ordinarytree']/*[@name]"):
 name=node.get('name');index=None
 for prefix in ['dg_node','state','connector']:
  if name.startswith(prefix) and name[len(prefix):].isdigit():index=int(name[len(prefix):]);break
 if index is None:continue
 path=f"/windows/window[@name='delveProgression']/rect[@name='skillcontent']/rect[@name='ordinarytree']/*[@name='{name}']"
 E.SubElement(root,'remove',xpath=path);app=E.SubElement(root,'append',xpath="/windows/window[@name='delveProgression']/rect[@name='skillcontent']/rect[@name='ordinarytree']")
 child=copy.deepcopy(node);child.set('visible','{dg_nodevisible'+str(index)+'}');app.append(child)
path="/windows/window[@name='delveProgression']/rect[@name='skillcontent']/simplebutton[@name='dg_toggleMastery']"
E.SubElement(root,'remove',xpath=path);app=E.SubElement(root,'append',xpath="/windows/window[@name='delveProgression']/rect[@name='skillcontent']")
child=copy.deepcopy(source.find(".//simplebutton[@name='dg_toggleMastery']"));child.set('visible','{dg_hasmasteries}');app.append(child);write('XUi_InGame/windows.xml',root)
loc={'delveTreeSummoning':'Summoning','delveSummoningFundamentalsRequired':'Requires Binding Discipline and Primal Bond.','delveForgedSummoningRod':'Forged Summoning Rod','delveForgedSummoningRodDesc':'Carpentry 20, upgraded Carpenter Bench. Uses existing Boar Summoning Runes. New boars have 25% more health and damage than the starter rod at equal rank and quality. Base duration 60 seconds; Enduring Pact extends it to 75. One summon per caster. Base durability 400; repair with Focus Repair Supplies.','delveSummoningRodDesc':'Field Crafting Mat starter rod. Summons one allied boar for 60 seconds using a Boar Summoning Rune. Summoning practice raises companion health and damage. Rank10 fundamentals and rank20 talents improve reloading, health, damage, toughness and duration. Rod quality improves health and damage. Recasting replaces the previous summon; repair with Focus Repair Supplies.'}
for i,n in enumerate(names):
 key='delvePerkSummoning'+n;loc[key]=titles[i];loc[key+'Desc']=descs[i]+' Costs one skill point. Companion bonuses are snapshotted on cast; recast after learning or respeccing.';loc[key+'Rank']='Requires Summoning '+str(10 if i<2 else 20)+'.'
with (M/'Config/Localization.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english']);[w.writerow([k,'Delve','','','',v]) for k,v in loc.items()]
if not P.exists():
 data=Path((B/'save-data-location.txt').read_text().strip());save=data/'Saves/Allium-v0.10/ForestTest02'
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 (A/'save-before.json').write_text(json.dumps({str(p.relative_to(save)):sha(p) for p in save.rglob('*') if p.is_file()},indent=2))
 with zipfile.ZipFile(A/'ForestTest02-before.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in save.rglob('*'):
   if p.is_file():z.write(p,'ForestTest02/'+p.relative_to(save).as_posix())
 shutil.copytree(save,P/'Saves/Allium-v0.10/ForestTest02')
 for e in json.loads((B/'manifest.json').read_text())['files']:
  n=e['path']
  if n.startswith(('Mods/','Worlds/')):
   dst=P/n.replace('Worlds/','GeneratedWorlds/',1);dst.parent.mkdir(parents=True,exist_ok=True)
   if n=='Mods/Delve/Delve.dll':shutil.copy2(A/'Delve.dll',dst)
   else:os.link(B/n,dst)
 shutil.copytree(R/'playtest/BatchEleven/Mods/StationProbe',P/'Mods/StationProbe')
 cfg=E.parse(str(R/'playtest/BatchEleven/serverconfig.xml'))
 for n,v in {'UserDataFolder':str(P),'ServerName':'Summoning Rank20 Verification','ServerPort':'29810','TelnetPort':'29819','TelnetPassword':uuid.uuid4().hex}.items():cfg.find(f"property[@name='{n}']").set('value',v)
 cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True);(P/'profile.json').write_text(json.dumps({'GamePath':'D:/Steam/steamapps/common/7 Days To Die'}))
else:shutil.copy2(A/'Delve.dll',P/'Mods/Delve/Delve.dll')
shutil.copytree(M,P/'Mods'/M.name,dirs_exist_ok=True)
print(P)
