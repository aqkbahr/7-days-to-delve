from pathlib import Path
import sys,json,copy,csv,shutil,os,uuid
from lxml import etree as E
sys.path.insert(0,str(Path(__file__).parent))
from build_station_progression import merge
R=Path(__file__).resolve().parents[1];A=R/'artifacts/summoning';A.mkdir(exist_ok=True)
B=Path(json.loads((R/'dist/active-playtest-release.json').read_text())['release']);(A/'base.txt').write_text(str(B))
M=R/'src/ZZZZZZZZZZZZZZZZZDelveSummoning';(M/'Config/XUi_InGame').mkdir(parents=True,exist_ok=True)
(M/'ModInfo.xml').write_text('<xml><Name value="DelveSummoning"/><DisplayName value="Delve - Forest Summoning"/><Version value="0.17.0"/><Author value="Delve"/></xml>')
def write(name,root):E.ElementTree(root).write(str(M/'Config'/name),pretty_print=True,encoding='utf-8',xml_declaration=True)
def prop(node,name,value):
 p=node.find("property[@name='%s']"%name)
 if p is None:p=E.SubElement(node,'property',name=name)
 p.set('value',str(value))
items=merge(B,'items');root=E.Element('configs');append=E.SubElement(root,'append',xpath='/items')
rod=copy.deepcopy(items.find("item[@name='delveMendingTotem']"));rod.set('name','delveSummoningRod');append.append(rod)
for n,v in dict(DescriptionKey='delveSummoningRodDesc',Tags='weapon,ranged,delveWeapon,delveMagic,delveSummoning',CustomIcon='delveStarterWand',CustomIconTint='170,220,110',UnlockedBy='',TintColor='170,220,110').items():prop(rod,n,v)
for e in list(rod.findall('effect_group')):rod.remove(e)
action=rod.find("property[@class='Action0']");prop(action,'Magazine_items','delveSummoningRune');prop(action,'Particles_muzzle_fire','')
effects=E.SubElement(rod,'effect_group',name='Summoning Rod')
for n,v in dict(EntityDamage=0,BlockDamage=0,MagazineSize=1,RoundsPerMinute=15,BurstRoundCount=1,ReloadSpeedMultiplier=1,DegradationMax=300,DegradationPerUse=1,MaxRange=4).items():E.SubElement(effects,'passive_effect',name=n,operation='base_set',value=str(v))
rune=copy.deepcopy(items.find("item[@name='delveHealingRune']"));rune.set('name','delveSummoningRune');append.append(rune)
for n,v in dict(DescriptionKey='delveSummoningRuneDesc',Tags='ammo,delveSummoning',CustomIconTint='170,220,110').items():prop(rune,n,v)
for e in list(rune.findall('effect_group')):rune.remove(e)
for item in [rod,rune]:
 for p in item.iter('property'):
  if p.get('value','').startswith('#@modfolder:'):p.set('value',p.get('value').replace('#@modfolder:','#@modfolder(ZDelvePresentation):'))
eg=E.SubElement(rune,'effect_group');E.SubElement(eg,'passive_effect',name='EntityDamage',operation='base_set',value='0');E.SubElement(eg,'passive_effect',name='BlockDamage',operation='base_set',value='0')
hand=E.SubElement(append,'item',name='meleeHandDelveSummonedBoar');prop(hand,'Extends','meleeHandAnimalWolf');eg=E.SubElement(hand,'effect_group');E.SubElement(eg,'passive_effect',name='EntityDamage',operation='base_set',value='6');E.SubElement(eg,'passive_effect',name='BlockDamage',operation='base_set',value='0');write('items.xml',root)
root=E.Element('configs');app=E.SubElement(root,'append',xpath='/entity_classes')
# Flatten native inheritance so the summon cannot inherit harvest drops or player-targeting AI.
native=E.parse('D:/Steam/steamapps/common/7 Days To Die/Data/Config/entityclasses.xml').getroot()
def flat(name):
 src=native.find("entity_class[@name='%s']"%name);out=flat(src.get('extends')) if src.get('extends') else E.Element('entity_class')
 for child in src:
  if not isinstance(child.tag,str):continue
  if child.tag=='property':
   old=out.find("property[@name='%s']"%child.get('name'))
   if old is not None:out.remove(old)
  out.append(copy.deepcopy(child))
 return out
boar=flat('animalBoar');boar.set('name','delveSummonedBoar');app.append(boar)
for child in list(boar):
 if child.tag in ['drop','effect_group'] or child.tag=='property' and child.get('name','').startswith(('AITask','AITarget')):boar.remove(child)
for n,v in dict(Class='Delve.EntityDelveSummon, Delve',Tags='entity,animal,delveSummon',EntityFlags='animal',Faction='whiteriver',IsEnemyEntity='false',UserSpawnType='None',HandItem='meleeHandDelveSummonedBoar',ExperienceGain=0,LootList='',LootDropProb=0,TimeStayAfterDeath=0,NavObject='',MoveSpeed=.8,MoveSpeedAggro='1.3,1.3',MapIcon='ui_game_symbol_tracking_pig',CompassIcon='ui_game_symbol_tracking_pig').items():prop(boar,n,v)
E.SubElement(boar,'property',name='AITask-1',value='ApproachAndAttackTarget',data='class=EntityZombie,0,EntityEnemyAnimal,0,EntityBandit,0')
prop(boar,'AITask-2','ApproachSpot');prop(boar,'AITask-3','Look');prop(boar,'AITarget-1','')
eg=E.SubElement(boar,'effect_group');E.SubElement(eg,'passive_effect',name='HealthMax',operation='base_set',value='80');write('entityclasses.xml',root)
root=E.Element('configs');app=E.SubElement(root,'append',xpath='/buffs')
for name in ['delveSkillSummoning','delveSummonStats']:
 b=E.SubElement(app,'buff',name=name,hidden='true');E.SubElement(b,'duration',value='0');E.SubElement(b,'stack_type',value='ignore')
 if name=='delveSummonStats':
  eg=E.SubElement(b,'effect_group');E.SubElement(eg,'passive_effect',name='HealthMax',operation='base_set',value='@delveSummonHealth')
write('buffs.xml',root)
root=E.Element('configs');app=E.SubElement(root,'append',xpath='/recipes')
for name,count,station,ingredients in [('delveSummoningRod',1,'delveFieldCraftingMat',{'resourceWood':30,'resourceCloth':8,'resourceBone':10}),('delveSummoningRune',5,'delveFieldCraftingMat',{'resourceRockSmall':10,'resourceBone':5,'resourceCropChrysanthemumPlant':2}),('delveSummoningRune',5,'delveInscriptionKit',{'resourceRockSmall':10,'resourceBone':5,'resourceCropChrysanthemumPlant':2})]:
 recipe=E.SubElement(app,'recipe',name=name,count=str(count),craft_area=station,craft_time='10')
 for n,c in ingredients.items():E.SubElement(recipe,'ingredient',name=n,count=str(c))
write('recipes.xml',root)
root=E.Element('configs')
for i in range(8):
 for attr,value in [('pos',f'28,{-171-i*48}'),('height','42')]:E.SubElement(root,'set',xpath=f"/windows/window[@name='delveProgression']/simplebutton[@name='dg_skill{i}']/@{attr}").text=value
app=E.SubElement(root,'append',xpath="/windows/window[@name='delveProgression']")
E.SubElement(app,'simplebutton',name='dg_skill8',pos='28,-555',width='180',height='42',caption='{dg_skilltext8}',font_size='17',depth='4',defaultcolor='38,49,60',hovercolor='67,84,96',bordercolor='70,86,98',visible='{dg_skillvisible8}');write('XUi_InGame/windows.xml',root)
with (M/'Config/Localization.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','english'])
 for k,v in {'delveSummoningRod':'Forest Summoning Rod','delveSummoningRune':'Boar Summoning Rune','delveSummonedBoar':'Bound Forest Boar','delveSummoningRodDesc':'Consumes one Boar Summoning Rune to call a weak allied Forest boar for 60 seconds. One per caster; recasting replaces it. Find open ground outside trader protection. Follows you and fights nearby enemies. Combat raises Summoning proficiency: +2 health per rank and +1 damage per 10 ranks. Rod quality adds 10% health and damage per quality above one. Craft at a Field Crafting Mat. Uses a borrowed wooden casting-focus model. Repair with Focus Repair Supplies.','delveSummoningRuneDesc':'Ammunition for the Forest Summoning Rod. One rune calls one boar for 60 seconds. No loot or harvest from summons. Craft five from 10 stone, 5 bone and 2 chrysanthemum at a Field Crafting Mat or Rune Bench.'}.items():w.writerow([k,'Delve','','','',v])
P=R/'playtest/Summoning'
if not P.exists():
 for e in json.loads((B/'manifest.json').read_text())['files']:
  n=e['path']
  if n.startswith(('Mods/','Worlds/')):
   dst=P/n.replace('Worlds/','GeneratedWorlds/',1);dst.parent.mkdir(parents=True,exist_ok=True)
   if n=='Mods/Delve/Delve.dll':shutil.copy2(A/'Delve.dll',dst)
   else:os.link(B/n,dst)
 shutil.copytree(R/'playtest/BatchTen/Saves',P/'Saves')
 shutil.copytree(R/'playtest/BatchTen/Mods/StationProbe',P/'Mods/StationProbe')
 cfg=E.parse(str(R/'playtest/BatchTen/serverconfig.xml'))
 for n,v in {'UserDataFolder':str(P),'ServerName':'Delve Summoning Verification','ServerPort':'29710','TelnetPort':'29719','TelnetPassword':uuid.uuid4().hex}.items():cfg.find(f"property[@name='{n}']").set('value',v)
 cfg.write(str(P/'serverconfig.xml'),encoding='utf-8',xml_declaration=True)
 (P/'profile.json').write_text(json.dumps({'GamePath':'D:/Steam/steamapps/common/7 Days To Die'}))
else:shutil.copy2(A/'Delve.dll',P/'Mods/Delve/Delve.dll')
shutil.copytree(M,P/'Mods'/M.name,dirs_exist_ok=True)
print('Summoning content and isolated profile ready:',P)

