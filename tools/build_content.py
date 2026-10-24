"""Author the 0.1 Living Border playtest content against the installed game.

Run with Python 3. No game installation files are written. The generated XML is
checked separately by validate_content.py before packaging.
"""
from pathlib import Path
from xml.etree import ElementTree as E
import csv
import argparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src/Delve/Config'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--game', default='D:/Steam/steamapps/common/7 Days To Die')
args = parser.parse_args()
base = Path(args.game) / 'Data/Config'
vanilla = {n: E.parse(base / (n + '.xml')) for n in ('items', 'entityclasses', 'entitygroups', 'progression')}
texts = {}

def loc(key, value):
    texts[key] = value
    return key

def node(container, tag, **attrs):
    return E.SubElement(container, tag, {k: str(v) for k, v in attrs.items()})

def prop(parent, name, value):
    return node(parent, 'property', name=name, value=value)

def effect(parent, name, value, operation='base_add', **attrs):
    return node(parent, 'passive_effect', name=name, operation=operation, value=value, **attrs)

def patch(target):
    root = E.Element('configs')
    return root, node(root, 'append', xpath='/' + target)

def save(name, root):
    E.indent(root, space='  ')
    E.ElementTree(root).write(OUT / (name + '.xml'), encoding='utf-8', xml_declaration=True)

items, item_append = patch('items')
recipes, recipe_append = patch('recipes')
buffs, buff_append = patch('buffs')
# Constitution replaces the native automatic health/stamina-per-level bonus.
for stat in ('HealthMax','StaminaMax'):
    node(buffs,'set',xpath=f"/buffs/buff/effect_group/passive_effect[@name='{stat}'][@value='@$PlayerLevelBonus']/@value").text='0'

def item(name, parent, title, desc, icon=None, tint=None):
    assert vanilla['items'].find(f".//item[@name='{parent}']") is not None, parent
    it = node(item_append, 'item', name=name)
    prop(it, 'Extends', parent)
    prop(it, 'CustomIcon', icon or parent)
    prop(it, 'DescriptionKey', loc(name+'Desc', desc))
    prop(it, 'CreativeMode', 'Player')
    if tint:
        prop(it, 'CustomIconTint', tint)
    loc(name, title)
    return it

def recipe(name, ingredients, station=None):
    r = node(recipe_append, 'recipe', name=name, count=1, craft_time=5)
    if station:
        r.set('craft_area', station)
    for ingredient, count in ingredients.items():
        node(r, 'ingredient', name=ingredient, count=count)
    return r

weapons = [
    ('delveBoneDagger','meleeWpnBladeT0BoneKnife','Wayfarer Dagger','Blades', {'resourceBone':5,'resourceYuccaFibers':5},1.05),
    ('delveOakCudgel','meleeWpnClubT0WoodenClub','Oak Cudgel','Blunt', {'resourceWood':15,'resourceYuccaFibers':5},1.05),
    ('delveAshSpear','meleeWpnSpearT0StoneSpear','Ashwood Spear','Polearms', {'resourceWood':15,'resourceRockSmall':8,'resourceYuccaFibers':5},1.05),
    ('delveBorderBow','gunBowT0PrimitiveBow','Border Scout Bow','Archery', {'resourceWood':20,'resourceYuccaFibers':15},1.05),
    ('delveIronDagger','meleeWpnBladeT1HuntingKnife','Forged Iron Dagger','Blades', {'resourceForgedIron':10,'resourceWood':5,'resourceLeather':3},1.12),
    ('delveIronMace','meleeWpnClubT1BaseballBat','Ironbound Mace','Blunt', {'resourceForgedIron':12,'resourceWood':15,'resourceLeather':3},1.12),
    ('delveIronSpear','meleeWpnSpearT1IronSpear','Borderguard Spear','Polearms', {'resourceForgedIron':12,'resourceWood':15,'resourceLeather':3},1.12),
    ('delveHuntingBow','gunBowT1WoodenBow','Ranger Bow','Archery', {'resourceWood':30,'resourceLeather':8,'resourceDuctTape':3},1.12),
]
for name, parent, title, skill, ingredients, damage in weapons:
    it = item(name, parent, title,
        f'A crafted weapon of the Living Border. Trains {skill} through damaging living enemies. '
        'Uses a familiar weapon model during this playtest. Improve quality with Border Smithing.', tint='190,210,155')
    prop(it, 'UnlockedBy', '')
    # Retain vanilla action tags so attacks, repair and weapon modifications work.
    source = vanilla['items'].find(f".//item[@name='{parent}']/property[@name='Tags']")
    if source is not None:
        prop(it, 'Tags', source.get('value') + ',delveWeapon,delve'+skill)
    eg = node(it, 'effect_group', name='Delve crafted weapon')
    effect(eg, 'EntityDamage', round(damage-1, 3), 'perc_add')
    recipe(name, ingredients)

it = item('delveEmberSalts','resourceCoal','Ember Salts',
          'A crafting reagent recovered by harvesting corrupted corpses. Used for warding supplies and tempered weapons.', tint='232,131,65')
prop(it, 'Stacknumber', 500)
prop(it, 'EconomicValue', 8)
prop(it, 'SellableToTrader', 'true')

for name, parent, title, ingredients, description in [
    ('delveHealingPoultice','medicalFirstAidBandage','Greenleaf Poultice',
     {'medicalBandage':1,'resourceYuccaFibers':10,'resourceCropChrysanthemumPlant':2},
     'A field dressing made with herbs. Provides the same treatment as a first-aid bandage.'),
    ('delveWayfarerTea','drinkJarRedTea','Wayfarer Tea',
     {'drinkJarBoiledWater':1,'resourceCropChrysanthemumPlant':2},
     'A restorative borderland tea. Provides the familiar hydration and digestion benefits of red tea.'),
]:
    it = item(name,parent,title,description,tint='150,210,140')
    prop(it,'UnlockedBy','')
    recipe(name,ingredients)

it = item('delveWardDraught','drinkJarRedTea','Ember Ward Draught',
          'Red tea fortified with ember salts. Grants 10 additional armor for three minutes. Does not remove biome hazards.', tint='235,170,85')
prop(it,'UnlockedBy','')
eg = node(it,'effect_group', name='Delve ward')
node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='delveWard')
recipe('delveWardDraught',{'drinkJarBoiledWater':1,'delveEmberSalts':3,'resourceCropChrysanthemumPlant':2})
b = node(buff_append,'buff',name='delveWard',name_key=loc('delveWard','Ember Ward'),description_key=loc('delveWardDesc','Your ward grants 10 armor for three minutes.'),icon='ui_game_symbol_armor')
node(b,'stack_type',value='replace'); node(b,'duration',value=180)
effect(node(b,'effect_group'),'PhysicalDamageResist',10)

# Heritage selection is irreversible in this playtest; an action requirement
# prevents consuming another heritage seal once the persistent choice is set.
heritages = [
    ('Human','PlayerExpGain',.05,'perc_add','5% more experience'),
    ('Elf','StaminaMax',10,'base_add','10 additional stamina'),
    ('Dwarf','CarryCapacity',3,'base_add','3 additional unencumbered slots'),
    ('Halfling','NoiseMultiplier',-.1,'perc_add','10% less noise'),
    ('Orc','HealthMax',10,'base_add','10 additional health'),
    ('Tiefling','HyperthermalResist',5,'base_add','5 additional heat resistance'),
]
for index, (name, stat, value, operation, description) in enumerate(heritages,1):
    key='delveHeritage'+name
    it=item(key,'questMaster',name+' Heritage Seal',
            f'Choose {name} heritage: {description}. Choose ONE heritage per character. This choice persists after death; no racial penalties or class locks.',tint='195,170,235')
    prop(it,'Stacknumber',1)
    ac=node(it,'property',**{'class':'Action0'})
    prop(ac,'Class','Eat'); prop(ac,'Delay',1); prop(ac,'UseAnimation','false')
    node(ac,'requirement',name='CVarCompare',cvar='delveHeritageChoice',operation='Equals',value=0)
    eg=node(it,'effect_group')
    node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='ModifyCVar',cvar='delveHeritageChoice',operation='set',value=index)
    node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff=key)
    recipe(key,{'resourceYuccaFibers':1})
    b=node(buff_append,'buff',name=key,name_key=loc(key+'Buff',name+' Heritage'),description_key=loc(key+'BuffDesc',description.capitalize()+'.'),icon='ui_game_symbol_add',remove_on_death='false')
    node(b,'stack_type',value='ignore'); node(b,'duration',value=0)
    effect(node(b,'effect_group'),stat,value,operation)

# All proficiencies are saved independently of purchased talents.
proficiencies = ['Blades','Blunt','Polearms','Archery','Wands','Staffs','Totems','Unarmed','HeavyArmor','MediumArmor','LightArmor','PackMule','Athletics','Stealth','Farming','Cooking','Mining','Smithing','Carpentry','Alchemy']
combat_tags = {'Blades':'bladeSkill','Blunt':'clubSkill,sledgeSkill,axe','Polearms':'spearSkill','Archery':'bowSkill,archery','Unarmed':'knuckleSkill','Wands':'delveWands','Staffs':'delveStaffs','Totems':'delveTotems'}
for skill in proficiencies:
    b=node(buff_append,'buff',name='delveSkill'+skill,name_key=loc('delveSkill'+skill,skill),description_key=loc('delveSkill'+skill+'Desc',
        f'{skill}: starts at 1, maximum 100. Meaningful practice advances this skill independently of talent points. Next rank costs 40 + 4 times current rank practice. Perk bands: 10/20/40/60/80/100. '+
        ('Each rank above 1 adds 0.2% matching damage.' if skill in combat_tags else 'Tree layouts are available in Skills. Entries marked NOT YET PLAYABLE are disabled while their behavior is implemented.')),
        icon='ui_game_symbol_agility',remove_on_death='false')
    node(b,'stack_type',value='ignore'); node(b,'duration',value=0)
    node(b,'display_value',value='delveLevel'+skill)
    eg=node(b,'effect_group')
    if skill in combat_tags: effect(eg,'EntityDamage','@delveBonus'+skill,'perc_add',tags=combat_tags[skill])

b=node(buff_append,'buff',name='delveAdvancement',name_key=loc('delveAdvancement','Attribute Points'),description_key=loc('delveAdvancementDesc',
    'Unspent attribute points. Buy Delve attribute ranks in Skills using this separate pool. +1 per level gained; +5 after Embers of Resistance. Base cap 20. Talent points buy perks. All proficiency starts at 1 and survives respec.'),icon='ui_game_symbol_add',remove_on_death='false')
node(b,'stack_type',value='ignore'); node(b,'duration',value=0)
node(b,'display_value',value='delveAttributePoints')

b=node(buff_append,'buff',name='delveWorldJournal',name_key=loc('delveWorldJournal','Allium: Living Border'),description_key=loc('delveWorldJournalDesc',
    'The number beside this journal is the shared count of corrupted enemies defeated in this world. When the Ashbound Warden falls, everyone receives the Warden Defeated entry. These world records survive restarts.'),icon='ui_game_symbol_challenge',remove_on_death='false')
node(b,'stack_type',value='ignore'); node(b,'duration',value=0)
node(b,'display_value',value='delveWorldKills')
b=node(buff_append,'buff',name='delveWardenVictory',name_key=loc('delveWardenVictory','Warden Defeated'),description_key=loc('delveWardenVictoryDesc',
    'Your world has defeated the Ashbound Warden. This victory belongs to everyone, including adventurers who arrive later. Further campaign chapters are still in development.'),icon='ui_game_symbol_challenge',remove_on_death='false')
node(b,'stack_type',value='ignore'); node(b,'duration',value=0)

# Three linked introductory quests; rewards start the next chapter.
quests, qa=patch('quests')
chapters=[
    ('delveArrival','The Living Border','Prepare to reclaim the frontier.',
     'Allium has fallen, but its people endure. Gather wood, stone and fibers. Craft a Wayfarer Dagger and Greenleaf Poultice, then prepare a Settlement Stone. Read the field guide description for the playtest route.',
     [('FetchKeep','resourceWood',20),('FetchKeep','resourceRockSmall',10),('FetchKeep','resourceYuccaFibers',20),('Craft','delveBoneDagger',1),('Craft','delveHealingPoultice',1)],
     [('casinoCoin',100),('medicalBandage',3)],'delveHearth'),
    ('delveHearth','A Hearth Against the Dark','Make the beginnings of a settlement.',
     'Craft a Settlement Stone, bedroll and campfire. Place them somewhere defensible. Stones use native player-owned claims; this playtest sets a two-active-claim limit. Workers and building decay are not active yet.',
     [('Craft','keystoneBlock',1),('Craft','bedroll',1),('Craft','campfire',1)],
     [('casinoCoin',150),('resourceForgedIron',12)],'delveEmbers'),
    ('delveEmbers','Embers of Resistance','Harvest the corruption and forge a ward.',
     'Find corrupted enemies in the wilderness. Harvest their corpses for Ember Salts, then craft an Ember Ward Draught. The Ashbound Warden is the first prototype incursion boss. A host can summon it early with: delve boss',
     [('FetchKeep','delveEmberSalts',3),('Craft','delveWardDraught',1)],
     [('casinoCoin',250),('resourceForgedIron',20)],None),
]
for qid,title,subtitle,desc,objectives,rewards,nextq in chapters:
    q=node(qa,'quest',id=qid)
    for key,value in [('name_key',loc(qid,title)),('subtitle_key',loc(qid+'Sub',subtitle)),('description_key',loc(qid+'Desc',desc)),('offer_key',qid+'Desc'),('icon','ui_game_symbol_hammer'),('category_key',loc('delveQuestCategory','Allium: Living Border')),('repeatable','false'),('shareable','false'),('add_to_tier_complete','false'),('completiontype','AutoComplete')]:
        prop(q,key,value)
    # All fetch objectives first; crafting phase starts only after gathering.
    for typ,ident,count in objectives:
        o=node(q,'objective',type=typ,id=ident,value=count,phase=1 if typ=='FetchKeep' else 2)
        if typ=='Craft':
            o.set('phase','2' if any(t=='FetchKeep' for t,_,_ in objectives) else '1')
            prop(o,'item',ident); prop(o,'count',count)
    node(q,'reward',type='Exp',value=500)
    for ident,count in rewards: node(q,'reward',type='Item',id=ident,value=count)
    if nextq: node(q,'reward',type='Quest',id=nextq)

it=item('delveFieldGuide','questMaster','Field Guide: The Living Border',
    'READ to start the three-chapter introduction. Choose a heritage by crafting one Heritage Seal. Search DELVE items in Creative or search weapon names in crafting. Six Delve attributes and Border talents appear in Skills. Defeat corrupted enemies and harvest Ember Salts. Host console: delve status; delve boss. This prototype uses vanilla terrain and models. Workers, full Allium reclamation, magic and the other nine bosses are not implemented.')
ac=node(it,'property',**{'class':'Action0'}); prop(ac,'Class','Quest'); prop(ac,'QuestGiven','delveArrival')
recipe('delveFieldGuide',{'resourceYuccaFibers':1})

# Six independent attributes, using native skill-point UI. Vanilla trees remain
# available while the complete replacement roster is designed and tested.
progression=E.Element('configs')
node(progression,'set',xpath='/progression/level/@max_level').text='80'
node(progression,'set',xpath='/progression/level/@skill_points_per_level').text='1'
atts=node(progression,'append',xpath='/progression/attributes')
skills=node(progression,'append',xpath='/progression/skills')
perks=node(progression,'append',xpath='/progression/perks')
attributes=[
 ('Strength','+1.5% melee damage, +2% mining/woodcutting block damage per point above 1; +1 unencumbered carrying slot per two points.',[
     ('EntityDamage',.015,'perc_add','melee'),('BlockDamage',.02,'perc_add','miningTool,harvestingTool')]),
 ('Dexterity','+1.5% archery damage, +1% weapon handling and crossbow reload speed, -1.5% noise per point above 1.',[
     ('EntityDamage',.015,'perc_add','bowSkill,archery'),('WeaponHandling',.01,'perc_add',None),('ReloadSpeedMultiplier',.01,'perc_add','bowSkill'),('NoiseMultiplier',-.015,'perc_add',None)]),
 ('Constitution','+5 health, +3 stamina and +1 physical armor rating per point above 1. Armor uses the native resistance cap.',[
     ('HealthMax',5,'base_add',None),('StaminaMax',3,'base_add',None),('PhysicalDamageResist',1,'base_add',None)]),
 ('Intelligence','+2% crafting speed, +1.5% magic ammunition damage and reload speed per point above 1.',[
     ('EntityDamage',.015,'perc_add','delveMagic'),('ReloadSpeedMultiplier',.015,'perc_add','delveMagic')]),
 ('Wisdom','+2% direct healing and medical treatment strength, -1% food/water use per point above 1. Spell regeneration awaits the magic system.',[
     ('EntityHeal',.02,'perc_add',None),('FoodLoss',-.01,'perc_add',None),('WaterLoss',-.01,'perc_add',None)]),
 ('Charisma','+1% buying and selling price modifiers per point above 1. Companion damage/health bonuses await assigned companions.',[
     ('BarteringBuying',.01,'base_add',None),('BarteringSelling',.01,'base_add',None)]),
]
for name,desc,effects in attributes:
    key='delveAtt'+name
    # Zero native cost prevents a native respec from converting attributes into
    # talent currency. The purchase patch charges one separate attribute point.
    a=node(atts,'attribute',name=key,name_key=loc(key,'Delve: '+name),desc_key=loc(key+'Desc',desc+' Costs separate attribute points; base rank 1 has no bonus.'),icon='ui_game_symbol_add',min_level=1,max_level=20,override_cost=','.join(['0']*20))
    eg=node(a,'effect_group')
    for stat,value,operation,tags in effects:
        fx=effect(eg,stat,f'{value},{round(value*19,4)}',operation,level='2,20')
        if tags: fx.set('tags',tags)
    ranks=','.join(str(r) for r in range(1,21))
    if name=='Strength': effect(eg,'CarryCapacity',','.join(str((r-1)//2) for r in range(1,21)),level=ranks)
    # Speed +38% means duration /1.38, not duration -38%.
    if name=='Intelligence': effect(eg,'CraftingTime',','.join(str(round(1/(1+.02*(r-1))-1,6)) for r in range(1,21)),'perc_add',level=ranks)
    for rank in range(1,21):
        node(eg,'effect_description',level=rank,desc_key=loc(key+str(rank),f'{name} {rank}'),long_desc_key=loc(key+str(rank)+'Long',f'{rank-1} points above baseline. {desc} Costs 1 attribute point.'))
    node(skills,'skill',name='delveSchool'+name,parent=key,name_key=loc('delveSchool'+name,'Border Talents'),icon='ui_game_symbol_hammer')

talents=[
 ('Smithing','Strength','Border Smithing','Craft Delve weapons at quality 2 / 3 / 4.', 'CraftingTier','1,2,3','base_add',','.join(w[0] for w in weapons)),
 ('Skirmisher','Dexterity','Skirmisher','Reduce weapon stamina cost by 5% / 10% / 15%.','StaminaLoss','-.05,-.1,-.15','perc_add',None),
 ('Endurance','Constitution','Hardy Adventurer','Gain 5 / 10 / 15 health.','HealthMax','5,10,15','base_add',None),
 ('Artisan','Intelligence','Patient Artisan','Reduce crafting time by 5% / 10% / 15%.','CraftingTime','-.05,-.1,-.15','perc_add',None),
 ('Forager','Wisdom','Trail Rations','Reduce food loss by 5% / 10% / 15%.','FoodLoss','-.05,-.1,-.15','perc_add',None),
 ('Trader','Charisma','Silver Tongue','Improve buying prices by 3% / 6% / 9%.','BarteringBuying','.03,.06,.09','base_add',None),
]
for name,parent,title,desc,stat,values,op,tags in talents:
    key='delveTalent'+name
    p=node(perks,'perk',name=key,parent='delveSchool'+parent,name_key=loc(key,title),desc_key=loc(key+'Desc',desc),icon='ui_game_symbol_hammer',max_level=3,override_cost='1,1,1')
    for rank,needed in [(1,1),(2,2),(3,3)]:
        req=node(p,'level_requirements',level=rank)
        node(req,'requirement',name='ProgressionLevel',progression_name='delveAtt'+parent,operation='GTE',value=needed,desc_key=loc(key+'Req'+str(rank),f'Requires Delve {parent} {needed}.'))
    eg=node(p,'effect_group'); fx=effect(eg,stat,values,op,level='1,2,3')
    if tags: fx.set('tags',tags)
    for rank in range(1,4):
        node(eg,'effect_description',level=rank,desc_key=loc(key+str(rank),f'{title} {rank}'),long_desc_key=key+'Desc')

for recipe_name in ('delveIronDagger','delveIronMace','delveIronSpear','delveHuntingBow'):
    texts[recipe_name+'Desc']+=' Crafting requires '+('Carpentry' if recipe_name=='delveHuntingBow' else 'Smithing')+' proficiency 20 in addition to normal recipe requirements.'

from progression_content import emit as emit_progression
emit_progression(progression, skills, perks, buff_append, node, effect, loc)
# Remove advertised quest point rewards as well as denying the runtime award.
node(quests,'set',xpath="/quests/quest/reward[@type='SkillPoints']/@value").text='0'

# Six first-wave enemies: inherited vanilla animations and AI, conservative stats.
entities, ea=patch('entity_classes')
enemies=[
 ('delveCorruptedWalker','zombieBoe','Corrupted Walker',130, .95,2),
 ('delvePossessedSoldier','zombieSoldier','Possessed Soldier',220,1,3),
 ('delveImp','zombieSpider','Imp',85,.75,1),
 ('delveHellhound','animalZombieDog','Hellhound',120,.90,2),
 ('delveDemonSpawn','zombieJoe','Demon Spawn',120,1,2),
 ('delveWarpedBrute','zombieFatHawaiian','Warped Brute',260,1.12,4),
 ('delveAshboundWarden','zombieBiker','Ashbound Warden',900,1.15,12),
]
for name,parent,title,health,size,salts in enemies:
    assert vanilla['entityclasses'].find(f".//entity_class[@name='{parent}']") is not None, parent
    en=node(ea,'entity_class',name=name,extends=parent)
    prop(en,'UserSpawnType','Menu'); prop(en,'Tags','entity,zombie,walker,delveCorrupted')
    prop(en,'SizeScale',size); prop(en,'ExperienceGain',200 if name!='delveAshboundWarden' else 1500)
    if name=='delveWarpedBrute': prop(en,'MoveSpeedAggro','.65,.85')
    if name=='delveAshboundWarden':
        prop(en,'MoveSpeedAggro','1,1.2'); prop(en,'LootDropProb',1)
    eg=node(en,'effect_group',name='Base Effects')
    effect(eg,'HealthMax',health,'base_set')
    node(en,'drop',event='Harvest',name='delveEmberSalts',count=salts)
    loc(name,title)

# Grant field guide only through the engine's new-character starter inventory.
for mode in ['GameModeSurvival','GameModeSurvivalSP','GameModeSurvivalMP']:
    xpath=f"/entity_classes/entity_class[@name='playerMale']/property[@class='ItemsOnEnterGame']/property[@name='{mode}']/@value"
    old=vanilla['entityclasses'].find(f".//entity_class[@name='playerMale']/property[@class='ItemsOnEnterGame']/property[@name='{mode}']").get('value')
    node(entities,'set',xpath=xpath).text=old+',delveFieldGuide,medicalBandage=2'

groups=E.Element('configs')
for group in ['ZombiesAll','ZombiesNight']:
    ga=node(groups,'append',xpath=f"/entitygroups/entitygroup[@name='{group}']")
    for name,weight in [('delveCorruptedWalker',2),('delveDemonSpawn',1.5),('delveImp',.5),('delvePossessedSoldier',.35),('delveWarpedBrute',.25)]:
        node(ga,'e',n=name,p=weight)
    if group=='ZombiesNight': node(ga,'e',n='delveHellhound',p=.3)
# Specific spawn group for predictable playtest encounters without replacing POIs.
ga=node(groups,'append',xpath='/entitygroups'); g=node(ga,'entitygroup',name='delveBorderPatrol')
for name in ['delveCorruptedWalker','delveDemonSpawn','delveHellhound']: node(g,'e',n=name)

# Keep native identifiers for maximum claim/currency compatibility.
loc('keystoneBlock','Settlement Stone')
loc('keystoneBlockDesc','A player-owned Settlement Stone using native land-claim protection and access. Delve limits each player to two active claims. NPC workers and magical building decay are not active in this playtest.')
loc('casinoCoin','Gold Coins')
loc('casinoCoinDesc','Gold coins used in trade throughout the borderlands. Uses the native currency system.')

from first_incursion import extend
gamestages = extend(base, groups, buff_append, node, effect, loc)
for name,root in [('items',items),('recipes',recipes),('buffs',buffs),('quests',quests),('progression',progression),('entityclasses',entities),('entitygroups',groups),('gamestages',gamestages)]: save(name,root)
with (OUT/'Localization.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f)
    w.writerow(['Key','File','Type','UsedInMainMenu','NoTranslate','KeepLoaded','english','Context / Alternate Text','german','spanish','french','italian','japanese','koreana','polish','brazilian','russian','turkish','schinese','tchinese'])
    for key,value in sorted(texts.items()): w.writerow([key,'Delve','', '', '', '', value]+['']*13)
# Explicitly remove our obsolete generated filename, never game localization.
if (OUT/'Localization.txt').exists(): (OUT/'Localization.txt').unlink()
print(f'Generated {len(texts)} localization entries, {len(weapons)} weapons, {len(enemies)} enemies, 3 quests, 6 heritages, 6 attributes and 6 talents.')


