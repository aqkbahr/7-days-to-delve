"""M1 catalogue plus explicit M0 ownership. Planned rows never become live recipes."""
import csv
import argparse
import json
from copy import deepcopy
from pathlib import Path
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game',default='D:/Steam/steamapps/common/7 Days To Die')
parser.add_argument('--mods',type=Path,default=ROOT/'src',help='Frozen mod folder for reproducible release validation')
options,_=parser.parse_known_args()
BASE = Path(options.game)/'Data/Config'
MODS = options.mods
OUT = ROOT/'src/Forest/catalogue.json'
pantry = {r['name']:r for r in json.loads((ROOT/'src/Forest/pantry.json').read_text())['recipes']}
readiness = {r['name']:r for r in json.loads((ROOT/'src/Forest/readiness.json').read_text())['recipes']} if (ROOT/'src/Forest/readiness.json').exists() else {}
farming_enabled = bool(E.parse(str(MODS/'Delve/Config/recipes.xml')).xpath("//recipe[@name='delveFarmHandbook']"))
farming_data = json.loads((ROOT/'src/Farming/first-pass.json').read_text()) if farming_enabled else {'recipes':[], 'stations':[], 'orders':[]}
farming = {r['name']:r for r in farming_data['recipes']}
processing_enabled=bool(E.parse(str(MODS/'Delve/Config/recipes.xml')).xpath("//recipe[@name='delveProcessingGuide']"))
processing_data=json.loads((ROOT/'src/Forest/processing.json').read_text()) if processing_enabled else {'recipes':[],'stations':[]}
processing={r['name']:r for r in processing_data['recipes']}
forged_enabled=bool(E.parse(str(MODS/'Delve/Config/recipes.xml')).xpath("//recipe[@name='delveForgedWand']"))
forged_data=json.loads((ROOT/'src/Forest/forged.json').read_text()) if forged_enabled else {'recipes':[]}
forged={r['name']:r for r in forged_data['recipes']}
SKILLS = ['Farming','Cooking','Mining','Smithing','Carpentry','Alchemy']

def merged(kind):
    tree = E.parse(str(BASE/(kind+'.xml')))
    for mod in ['Delve','DelveWayrest','DelveWildlife','ZDelveForest']:
        path = MODS/f'{mod}/Config/{kind}.xml'
        if not path.exists(): continue
        for op in E.parse(str(path)).getroot():
            targets=tree.xpath(op.get('xpath'))
            assert targets, (path,op.get('xpath'))
            for t in targets:
                if op.tag=='append':
                    for n in op:t.append(deepcopy(n))
                elif op.tag=='set':
                    if getattr(t,'is_attribute',False):t.getparent().set(t.attrname,op.text or '')
                    else:t.text=op.text or ''
                elif op.tag=='remove':t.getparent().remove(t)
                else:raise ValueError(op.tag)
    return tree

native_owner = {
 'resourceCloth':'Carpentry','resourceLeather':'Carpentry','resourceGlue':'Alchemy','resourceDuctTape':'Carpentry',
 'resourceForgedIron':'Smithing','resourceScrapIron':'Smithing','resourceNail':'Smithing','resourceMetalPipe':'Smithing','resourceArrowHeadIron':'Smithing',
 'resourceCobblestones':'Mining','resourceCrushedSand':'Mining','foodCornMeal':'Cooking','medicalBandage':'Alchemy',
 'drinkJarBoiledWater':'Cooking','ammoArrowStone':'Carpentry','ammoArrowIron':'Carpentry','ammoCrossbowBoltIron':'Carpentry','ammoCrossbowBoltStone':'Carpentry',
 'farmPlotBlockVariantHelper':'Farming','campfire':'Carpentry','forge':'Smithing','workbench':'Carpentry',
 'bedroll':'Carpentry','keystoneBlock':'Carpentry','woodLogPillar100':'Carpentry',
 'meleeToolRepairT0StoneAxe':'Carpentry','meleeToolPickT1IronPickaxe':'Smithing',
 'meleeToolAxeT1IronFireaxe':'Smithing','meleeToolShovelT0StoneShovel':'Carpentry',
 'woodSecureChest':'Carpentry','woodDoor1':'Carpentry',
}
for seed in ['Corn','Potato','Pumpkin','Mushroom','Blueberry','Cotton','Chrysanthemum','Goldenrod']:
    native_owner['planted'+seed+'1']='Farming'
def owner(name):
    if name.startswith('delveLesson') and name.endswith('Notes'):return None
    if name in ('delveRecruitLedger','delveRallyFlag','delveRecoveryShrine'):return 'Carpentry'
    if name in readiness:return readiness[name]['skill']
    if name in forged:return forged[name]['skill']
    if name in processing:return processing[name]['skill']
    if name in farming:return farming[name]['skill']
    if name in pantry:return pantry[name]['skill']
    if name in native_owner:return native_owner[name]
    if name in ['delveFieldGuide'] or name.startswith('delveHeritage'):return None
    if name in ['delveOakCudgel','delveAshSpear','delveLeatherKnuckles']:return 'Carpentry'
    if name=='delveBoneDagger':return 'Smithing' # weapon assembly; bone grade is explicitly included
    if name=='delveEmberSalts' or 'Rune' in name or 'Poultice' in name or 'Draught' in name:return 'Alchemy'
    if 'Tea' in name:return 'Cooking'
    if name.startswith('armorDelve'):return 'Smithing' if 'Heavy' in name else 'Carpentry'
    if any(x in name for x in ['Bow','Wand','Staff','Totem']):return 'Carpentry'
    if name.startswith('delveIron'):return 'Smithing'
    raise ValueError('Unclassified recipe '+name)

routes={}
def route(ids,skill,source,alternate,availability='renewable'):
    for id in ids.split():routes[id]=dict(id=id,harvest_skill=skill,source=source,alternate=alternate,availability=availability)
route('resourceWood','Carpentry','Forest trees and fallen wood','Native wooden salvage')
route('resourceYuccaFibers','Farming','Forest grass','Native vegetation salvage')
route('resourceRockSmall resourceClayLump resourceScrapIron resourceCoal resourceLead resourcePotassiumNitratePowder','Mining','Forest terrain/rocks; marked iron/coal/lead/nitrate deposits on Allium','POI loot, salvage or trader supplies; inspect actual stock','world deposits')
route('resourceOilShale','Mining','Drylands ore; NOT a required Forest input','Early oil proposals use animal fat','later biome')
route('resourceLeather resourceBone resourceAnimalFat foodRawMeat resourceFeather','Farming','Native animals harvested with suitable tools; feathers also in nests','POI loot/trader supplies; special hides convert to leather')
route('foodRottingFlesh','Farming','Native corpse harvest and loot','Trader/POI supply where present')
route('resourceCropCottonPlant resourceCropChrysanthemumPlant resourceCropGoldenrodPlant foodCropCorn foodCropPotato foodCropPumpkin foodCropMushrooms foodCropBlueberries','Farming','Wild Forest plants and three authored Forest pantry gardens; seeds can be replanted','Native food/seed loot and traders')
route('foodDelveBrambleberries resourceDelveYarrow resourceDelveThyme resourceDelveMooncap','Farming','Wild Forest plants and the three pantry gardens; cultivated crops return seeds','Two ingredients craft a seed; inspect garden locations in pantry guide')
route('foodHoney',None,'Native stump harvest/loot; not a guaranteed drop','Trader honey when stocked; choose other meals if unavailable','optional ingredient')
route('drinkJarRiverWater',None,'Native murky-water loot/collection systems','Trader water; renewable water works is an M2/M5 deliverable','native supply; manual route verification required')
route('delveEmberSalts',None,'Harvest corrupted enemies','Convert Forest Crystals through Alchemy')
route('delveThornhide delveGloomPelt delveForestCrystal','Farming','Thornback/Gloomcat/Crystal Stag corpse harvest, respectively','Optional substitutes only; no essential recipe may depend on a rare beast','rare optional')
route('resourceMechanicalParts',None,'Native mechanical salvage or loot','Trader supplies; essential upgraded Forest stations will use planned iron fittings','native supply')
route('unit_iron unit_clay',None,'Native forge internal smelting inventory','Use the native recipe variant appropriate to the server smelting setting','station internal')
route('unit_glass',None,'Native forge internal glass inventory from sand/glass','Crushed-sand terrain recipe is the early alternative','optional station internal')
route('foodCropGraceCorn','Farming','Rare Wasteland crop; not required in Forest','Use bone-based glue recipe instead','later-biome alternative only')

stations=[
 dict(id='cementMixer',status='native alternative',module=None,source='Optional native crushed-sand recipe; gather sand directly for the Forest route',fuel='native rules'),
 dict(id='inventory',status='live',module=None,source='Available on a new character',fuel=None),
 dict(id='campfire',status='live',module='Native cooking pot/grill when recipe requires',source='Craft campfire; Wayrest hearth; pot acquisition must be walked',fuel='wood or compatible native fuel'),
 dict(id='forge',status='live',module='Native tools when recipe requires',source='Wayrest forge; own forge uses native knowledge and recipe',fuel='wood/coal'),
 dict(id='workbench',status='live',module=None,source='Wayrest workbench; own bench uses native knowledge and recipe',fuel=None),
 dict(id='chemistryStation',status='native alternative',module=None,source='Optional native station, not required for Forest catalogue completion',fuel='native rules'),
]
for station in farming_data['stations']:
    stations.append(dict(id=station['name'],status='live',module=None,
        source=f"Craft in inventory at character level {station['level']}",fuel=None))
if farming_enabled:
    route('resourceCropAloeLeaf','Farming','Wild desert aloe; renewable cultivated aloe','Native aloe/seed loot or traders')
knowledge=[dict(id='known',source='Known starter recipe',fallback='None required',status='live'),
 dict(id='native_knowledge',source='Native books/knowledge where learnable',fallback='Existing trader/loot systems; deterministic Forest replacement planned',status='live'),
 dict(id='forge_notes',source='Missing Anvil project',fallback='Steward purchase: proposed 300 gold',status='planned'),
 dict(id='workshop_notes',source='Weaver/woodworker recovery project',fallback='Steward purchase: proposed 300 gold',status='planned'),
 dict(id='rune_notes',source='Rune Tracings recovery',fallback='Steward purchase: proposed 300 gold',status='planned'),
 dict(id='quarry_notes',source='Quarry Contract',fallback='Steward purchase: proposed 200 gold',status='planned'),
 dict(id='provision_notes',source='Winter Larder project',fallback='Steward purchase: proposed 200 gold',status='planned')]

items=merged('items'); blocks=merged('blocks'); recipes=merged('recipes')
for s in processing_data['stations']:
    stations.append(dict(id=s['name'],status='live',module=None,source='Craft known recipe at stated skill; no book needed',fuel='Heated recipes consume charcoal ingredients; no separate fuel slot'))
local={}
for m in ['Delve','ZDelveForest']:
    with (MODS/f'{m}/Config/Localization.csv').open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):local[row['Key']]=row.get('english',row['Key'])
authored=set()
for m in ['Delve','ZDelveForest']:
    authored.update(n.get('name') for n in E.parse(str(MODS/f'{m}/Config/recipes.xml')).xpath('//append/recipe'))
rows=[]
def details(name):
    n=items.find(f"item[@name='{name}']")
    if n is None:n=blocks.find(f"block[@name='{name}']")
    if n is None:return {}
    chain=[]; seen=set()
    while n is not None:
        key=n.get('name')
        if key in seen:raise ValueError('Circular item inheritance '+key)
        seen.add(key); chain.insert(0,n)
        parent=n.find("property[@name='Extends']")
        if parent is None:break
        parent_name=parent.get('value')
        n=items.find(f"item[@name='{parent_name}']")
        if n is None:n=blocks.find(f"block[@name='{parent_name}']")
    properties={}; effects=[]
    for definition in chain:
        properties.update({p.get('name'):p.get('value') for p in definition.findall('property') if p.get('name')})
        effects.extend([dict(p.attrib,defined_by=definition.get('name')) for p in definition.findall('.//passive_effect')])
    return dict(inheritance=[d.get('name') for d in chain],properties=properties,effects=effects,
                interpretation='Inherited property values; effect declarations retain source and quality conditions, not computed combat totals')

for n in recipes.findall('recipe'):
    name=n.get('name')
    if name not in authored and name not in native_owner and name not in farming and name not in processing:continue
    if n.find('wildcard_forge_category') is not None:continue # salvage isn't a production recipe
    if n.find("ingredient[@name='resourceLegendaryParts']") is not None:continue # native quality-six variant outside this slice
    rank=forged.get(name,processing.get(name,pantry.get(name,{}))).get('rank',20 if name in ['delveIronDagger','delveIronMace','delveIronSpear','delveHuntingBow'] else 1)
    data=details(name)
    rows.append(dict(id=name+':'+str(sum(r['output']==name for r in rows)),output=name,
        title=local.get(name,name),status='live mod' if name in authored else 'live native',primary_skill=owner(name),
        proficiency=rank,grade='Forged' if rank==20 else 'Field',knowledge='native_knowledge' if 'learnable' in n.get('tags','') else 'known',
        station=n.get('craft_area','inventory'),station_tool=n.get('craft_tool'),inputs={i.get('name'):int(i.get('count')) for i in n.findall('ingredient')},
        output_count=int(n.get('count','1')),seconds=n.get('craft_time','native default'),fuel='native station rules' if n.get('craft_area') else None,
        stats=data,repair=data.get('properties',{}).get('RepairTools','inherit native parent; consumables cannot be repaired'),
        economy='Existing native/mod economy; inherited salvage must be verified before cost-savings perks expand',
        acquisition='Known mod recipe at stated proficiency' if name in authored else 'Native recipe conditions apply',
        first_use=('Character '+str(farming[name]['level'])+' unlock') if name in farming else ('Character 1-5' if rank==1 else 'Character 6-20 target, proficiency-gated'),upgrade_of=None,
        character_level=farming.get(name,{}).get('level',1)))

def plan(id,title,skill,rank,station,inputs,stats,count=1,knowledge_id='known',repair=None,upgrade=None):
    if id in farming or id in processing or id in forged:return # Superseded by implemented recipes.
    rows.append(dict(id=id+':planned',output=id,title=title,status='planned M2-M5',primary_skill=skill,proficiency=rank,
        grade='Forged' if rank==20 else 'Field',knowledge=knowledge_id,station=station,station_tool=None,inputs=inputs,
        output_count=count,seconds=20 if rank<20 else 40,fuel='1 wood per batch' if station in ['forge','delveForgeAnvil'] else None,
        stats=stats,repair=({'item':repair,'count':1,'restoration':'full durability; provisional target'} if repair else None),economy='Unsellable during balance test; no salvage until explicit loss-making return is authored',
        acquisition='Craft after specified knowledge and station; quantities/stats are first-playtest targets',
        first_use='Character 6-10 target' if rank<20 else 'Character 11-20 target',upgrade_of=upgrade))

for id,title,skill,ingredients in [
 ('delveForgeAnvil','Forge Anvil','Smithing',{'resourceForgedIron':8,'resourceWood':10}),
 ('delveOutfittingKit','Outfitting Kit','Carpentry',{'resourceWood':20,'resourceCloth':8,'resourceBone':4}),
 ('delveSawKit','Saw and Seasoning Rack','Carpentry',{'resourceForgedIron':4,'resourceWood':20}),
 ('delveMortarKit','Mortar and Brewing Kit','Alchemy',{'resourceRockSmall':20,'resourceClayLump':10,'resourceWood':5}),
 ('delveSortingTable','Ore Sorting Table','Mining',{'resourceWood':20,'resourceRockSmall':20}),
 ('delveInscriptionKit','Rune Inscription Kit','Alchemy',{'resourceRockSmall':10,'resourceCloth':4,'resourceForgedIron':2})]:
    plan(id,title,skill,10,'inventory',ingredients,{'capability':'Unlock matching catalogue processing; no blanket yield bonus'})
    if not any(s['id']==id for s in stations):stations.append(dict(id=id,status='planned',module=title,source='Craft module in inventory; placement/tool-slot mechanism requires M2 implementation',fuel=None))

components=[
 ('delveRoughHandle','Rough Handle','Carpentry',1,'inventory',{'resourceWood':6},2),
 ('delveLeatherBinding','Leather Binding','Carpentry',1,'inventory',{'resourceLeather':2},4),
 ('delveSeasonedTimber','Seasoned Timber','Carpentry',10,'delveSawKit',{'resourceWood':12},4),
 ('delveCuredLeather','Cured Leather','Carpentry',10,'delveOutfittingKit',{'resourceLeather':4,'resourceWood':2},2),
 ('delveWovenCloth','Woven Cloth','Carpentry',10,'delveOutfittingKit',{'resourceCloth':4},2),
 ('delveIronFittings','Iron Fittings','Smithing',10,'forge',{'resourceForgedIron':2},4),
 ('delveDressedStone','Dressed Stone','Mining',10,'delveSortingTable',{'resourceRockSmall':10},4),
 ('delveIronConcentrate','Iron Concentrate','Mining',20,'delveSortingTable',{'resourceScrapIron':20},1),
 ('delveHerbalExtract','Herbal Extract','Alchemy',10,'delveMortarKit',{'resourceDelveYarrow':2,'resourceDelveThyme':1},2),
 ('delveRuneBlank','Rune Blank','Mining',10,'delveSortingTable',{'resourceRockSmall':5},10),
 ('delveCompost','Compost','Farming',10,'inventory',{'foodRottingFlesh':2,'resourceYuccaFibers':10},2),
 ('delveCharcoal','Charcoal','Smithing',10,'campfire',{'resourceWood':10},5),
 ('delveHideRepair','Hide Repair Supplies','Carpentry',10,'inventory',{'resourceLeather':2,'resourceCloth':2},2),
 ('delveMetalRepair','Metal Repair Supplies','Smithing',10,'inventory',{'resourceScrapIron':10,'resourceCloth':2},2),
 ('delveFocusRepair','Focus Repair Supplies','Carpentry',10,'inventory',{'resourceWood':5,'resourceCloth':2},2),
]
for id,title,skill,rank,station,ingredients,count in components:
    plan(id,title,skill,rank,station,ingredients,{'role':'Processing/component or repair supply; no combat modifier'},count)
plan('resourceForgedIron','Concentrate-forged Iron','Smithing',20,'delveForgeAnvil',{'delveIronConcentrate':1,'resourceClayLump':2,'delveCharcoal':1},
     {'role':'Additional planned recipe yielding actual forged iron; no new ingot currency'},2,'forge_notes')

for suffix,title,parent,skill,station,inputs,repair,stats in [
 ('Dagger','Balanced Iron Dagger','delveIronDagger','Smithing','delveForgeAnvil',{'resourceForgedIron':10,'delveRoughHandle':1,'delveLeatherBinding':2},'delveMetalRepair',{'damage_vs_starter':1.2,'durability':300}),
 ('Mace','Balanced Iron Mace','delveIronMace','Smithing','delveForgeAnvil',{'resourceForgedIron':12,'delveRoughHandle':2,'delveLeatherBinding':2},'delveMetalRepair',{'damage_vs_starter':1.2,'durability':300}),
 ('Spear','Balanced Iron Spear','delveIronSpear','Smithing','delveForgeAnvil',{'resourceForgedIron':10,'delveSeasonedTimber':3,'delveLeatherBinding':2},'delveMetalRepair',{'damage_vs_starter':1.2,'durability':300}),
 ('Knuckles','Reinforced Handwraps','delveLeatherKnuckles','Carpentry','delveOutfittingKit',{'delveCuredLeather':4,'delveWovenCloth':2,'delveIronFittings':2},'delveHideRepair',{'damage_vs_starter':1.2,'durability':300}),
 ('Bow','Seasoned Longbow','delveHuntingBow','Carpentry','delveSawKit',{'delveSeasonedTimber':6,'delveLeatherBinding':4},'delveFocusRepair',{'damage_vs_starter':1.2,'durability':300}),
 ('Crossbow','Border Crossbow',None,'Carpentry','delveSawKit',{'delveSeasonedTimber':6,'delveIronFittings':4,'delveLeatherBinding':4},'delveFocusRepair',{'single_shot_damage_vs_starter_bow':1.35,'role':'Slower reload; native bolts','durability':300}),
 ('Wand','Carved Spark Wand','delveStarterWand','Carpentry','delveSawKit',{'delveSeasonedTimber':4,'delveWovenCloth':2,'delveIronFittings':2},'delveFocusRepair',{'capacity':10,'damage_vs_starter':1.1,'durability':300}),
 ('Staff','Carved Ember Staff','delveStarterStaff','Carpentry','delveSawKit',{'delveSeasonedTimber':6,'delveWovenCloth':2,'delveIronFittings':2},'delveFocusRepair',{'capacity':1,'damage_vs_starter':1.15,'durability':300,'area_payload':'Separate rune implementation, not automatic on tool'}),
 ('Totem','Carved Hex Totem','delveStarterTotem','Carpentry','delveSawKit',{'delveSeasonedTimber':4,'delveWovenCloth':2,'delveLeatherBinding':2},'delveFocusRepair',{'capacity':5,'damage_vs_starter':1.1,'durability':300}),
 ('MendingTotem','Carved Mending Totem','delveMendingTotem','Carpentry','delveSawKit',{'delveSeasonedTimber':4,'delveWovenCloth':2,'delveLeatherBinding':2},'delveFocusRepair',{'capacity':5,'base_healing':22,'durability':300}),
]:
    plan('delveForged'+suffix,title,skill,20,station,inputs,stats,knowledge_id='forge_notes' if skill=='Smithing' else 'workshop_notes',repair=repair,upgrade=parent)
for category,material,armor,penalty in [('Light','delveWovenCloth',8,0),('Medium','delveCuredLeather',12,.025),('Heavy','resourceForgedIron',15,.05)]:
    for slot in ['Helmet','Outfit','Gloves','Boots']:
        plan('armorDelveForged'+category+slot,'Forged-grade '+category+' '+slot,'Smithing' if category=='Heavy' else 'Carpentry',20,
             'delveForgeAnvil' if category=='Heavy' else 'delveOutfittingKit',{material:6,'delveLeatherBinding':2},
             {'armor':armor,'mobility_penalty':penalty,'durability':300,'mod_slots':1},knowledge_id='forge_notes' if category=='Heavy' else 'workshop_notes',
             repair='delveMetalRepair' if category=='Heavy' else 'delveHideRepair',upgrade='armorDelve'+category+slot)
for suffix,parent in [('Pickaxe','meleeToolPickT1IronPickaxe'),('Axe','meleeToolAxeT1IronFireaxe'),('Shovel','meleeToolShovelT0StoneShovel')]:
    plan('delveForged'+suffix,'Border '+suffix,'Smithing',20,'delveForgeAnvil',{'resourceForgedIron':10,'delveRoughHandle':2,'delveLeatherBinding':2},
         {'natural_block_damage_vs_basic':1.25,'durability':300},knowledge_id='forge_notes',repair='delveMetalRepair',upgrade=parent)
for kind,stats in [('Wand',{'direct_damage':22}),('Staff',{'direct_damage':30,'radius_m':2,'splash_damage':12,'block_damage':0,'friendly_fire':'respect server setting'}),
                   ('Hex',{'direct_damage':12,'slow_percent':20,'duration_seconds':6}),('Healing',{'base_heal':25,'target':'self; ally targeting is separate M3 work'}),
                   ('Ward',{'armor_bonus':8,'duration_seconds':30,'stacking':'refresh only','requires':'protective totem action, M3'})]:
    plan('delveEtched'+kind+'Rune','Etched '+kind+' Runes','Alchemy',20,'delveInscriptionKit',{'delveRuneBlank':10,'delveHerbalExtract':2,'delveEmberSalts':1},stats,10,'rune_notes')
plan('delveWardTotem','Protective Totem','Carpentry',20,'delveSawKit',{'delveSeasonedTimber':4,'delveWovenCloth':2,'delveLeatherBinding':2},
     {'capacity':4,'ammo':'delveEtchedWardRune','damage':0},knowledge_id='workshop_notes',repair='delveFocusRepair')
plan('foodDelveTrailRations','Forest Trail Rations','Cooking',20,'campfire',{'foodRawMeat':2,'foodDelveBrambleberries':2},
     {'food':25,'water':0,'stack':20,'meal_buff':'none; carrying convenience'},2,'provision_notes')
plan('foodDelveGathererPorridge','Gatherer Porridge','Cooking',20,'campfire',{'foodCornMeal':2,'drinkJarBoiledWater':1,'resourceDelveThyme':1},
     {'food':30,'water':10,'meal_buff':'10% less gathering stamina cost, 10 minutes; single meal slot'},1,'provision_notes')
plan('foodDelveIncursionSupper','Incursion Supper','Cooking',20,'campfire',{'foodRawMeat':2,'foodCropPotato':2,'drinkJarBoiledWater':1,'resourceDelveThyme':1},
     {'food':50,'water':10,'meal_buff':'+15 maximum stamina for 15 minutes; replaces other meal buff'},1,'provision_notes')
plan('delveArborProtection','Arbor Protection Draught','Alchemy',20,'delveMortarKit',{'drinkJarBoiledWater':1,'delveEmberSalts':3,'resourceDelveYarrow':2},
     {'effect':'10 minutes of actual Burnt Arbor hazard protection; verify native hazard buff binding before shipping','not_equivalent':'Ember Ward armor buff'},1,'rune_notes')

# Resources describe raw acquisition and processing; unresolved sources fail closed.
outputs={r['output'] for r in rows}
missing={i for r in rows for i in r['inputs'] if i not in routes and i not in outputs}
if missing:raise ValueError('Missing ingredient acquisition '+str(sorted(missing)))
for output in outputs:
    if output not in routes:
        rr=[r for r in rows if r['output']==output]
        routes[output]=dict(id=output,harvest_skill=None,source='Craft through catalogue recipe(s): '+', '.join(r['id'] for r in rr),
                           alternate='Native loot where applicable; not assumed for planned items',availability='planned' if all(r['status'].startswith('planned') for r in rr) else 'craftable')

gardens=[]
for g in E.parse(str(ROOT/'artifacts/validation/pantry-world-cells.xml')).getroot():
    gardens.append(dict(prefab=g.get('name'),cells=[dict(c.attrib) for c in g]))
catalogue=dict(schema_version=1,scope='Forest M0/M1: live baseline plus authored Field/Forged target; planned rows are NOT enabled',
 deterministic_supply_targets=[
    dict(resource='drinkJarRiverWater',status='planned M2/M5',route='Wayrest public well: collect one murky water per interaction, 10 second server cooldown, no item input',fallback='Steward sells 10 daily at proposed 2 gold each; native boiling still required'),
    dict(resource='toolCookingPot',status='planned M2/M5',route='First hearth lesson grants one pot once per character',fallback='Steward always restocks one daily at proposed 50 gold'),
    dict(resource='native_knowledge',status='planned M5',route='Replace required Forest RNG knowledge gates with the listed recovery projects',fallback='Priced steward notes listed under knowledge; no rare-drop-only essential unlock')],
 source_locations=dict(gardens=gardens,ore_manifest='src/Worlds/Allium/resource-sites.json',
    world='Allium-v0.9',wayrest_steward=[-2681,65,-2133],
    limits='Location data is authored; walking distances, resource yield and availability require human acceptance'),
 stations=stations,knowledge=knowledge,resources=sorted(routes.values(),key=lambda r:r['id']),recipes=rows,
 contracts=[dict(id=k['id'],source=k['source'],alternate=k['fallback'],status=k['status']) for k in knowledge if k['status']=='planned'],
 farming_orders=farming_data['orders'],
 balance_policy=dict(character_level='Farming recipes have explicit character-level gates; other recipes retain their proficiency gates and pacing targets',proficiency='1-20',
  talent_points_at_character_20=20,attribute_points_with_tutorial=24,planned_values='First-playtest targets; not validated balance',
  early_native_recipes='Preserved; planned replacements do not remove live access',
  forge_settings='Native smelting/replacement alternatives are distinct rows, not simultaneously granted outputs',
  raw_materials='Renewable crops/animals plus finite world deposits; travel yields need manual acceptance'))
if processing_enabled:
    catalogue['scope']='Forest M2: live processing, farming and supplies; remaining equipment/protection targets are NOT enabled'
    catalogue['deterministic_supply_targets']=[
        dict(resource='drinkJarRiverWater',status='live',route='Craft Forest Rain Collector from wood, cloth and stone; place under open sky and insert clay-fired empty jars',fallback='Native murky-water loot; boil at the Field Hearth with charcoal'),
        dict(resource='toolCookingPot',status='live',route='Forest Forge: 20 scrap iron and 2 charcoal; no book required',fallback='Field Hearth boiling and processing do not require a pot'),
        dict(resource='processing_knowledge',status='live',route='M2 processing recipes use explicit skill gates with no book or rare-drop requirements',fallback='Later equipment knowledge projects remain planned')]
    for resource in catalogue['resources']:
        if resource['id']=='drinkJarRiverWater':resource.update(source='Forest Rain Collector with empty jars; outdoors, 0.5-1 game hour per slot',alternate='Native loot',availability='renewable collector production')
        if resource['id']=='delveEmberSalts':resource.update(source='Corrupted corpse harvest or Mooncaps plus charcoal at Apothecary Bench',alternate='Forest Crystal conversion',availability='renewable harvest or cultivated ingredients')
if forged_enabled:catalogue['scope']='Forest integration source: Forged equipment and Arbor protection definitions included; runtime acceptance is recorded separately'
OUT.write_text(json.dumps(catalogue,indent=2)+'\n',encoding='utf-8')

# Only live rows drive ownership. Native recipes retain their existing knowledge.
mapping={r['output']:r['primary_skill'] for r in rows if not r['status'].startswith('planned') and r['primary_skill']}
harvest={k:v['harvest_skill'] for k,v in routes.items() if v['harvest_skill']}
code=['// Generated by build_forest_catalogue.py. Planned recipes are excluded.','namespace Delve { public static class ForestRecipeOwnership {']
for method,data in [('Skill',mapping),('Harvest',harvest)]:
    code+=['public static string '+method+'(string name) { switch((name ?? "").ToLowerInvariant()) {']
    code += ['case '+json.dumps(k.lower())+': return '+json.dumps(v)+';' for k,v in sorted(data.items())]
    code+=['default:return null; } }']
code+=['} }']
(ROOT/'src/Code/ForestRecipeOwnership.generated.cs').write_text('\n'.join(code)+'\n',encoding='utf-8')
lines=['FOREST CRAFTING AND RESOURCE CATALOGUE - '+('M3' if forged_enabled else 'M2' if processing_enabled else 'M0/M1'),'',catalogue['scope'],'',
       'LIVE = present in baseline. PLANNED = authored target for later milestones, unavailable in crafting today.',
       'Numeric planned costs/stats are first-playtest targets. Native quality/knowledge/forge settings still apply.','']
for skill in SKILLS+[None]:
    lines += [(skill or 'ONBOARDING')+' RECIPES','']
    for r in rows:
        if r['primary_skill']!=skill:continue
        lines += [r['title']+' ['+r['id']+'] - '+r['status'],
            f"  Skill {r['proficiency']}; character {r.get('character_level',1)}; {r['grade']}; station {r['station']}; tool {r['station_tool'] or 'none'}; knowledge {r['knowledge']}",
            '  Inputs: '+', '.join(f'{v} {k}' for k,v in r['inputs'].items())+f" -> {r['output_count']} output; time {r['seconds']} sec; fuel {r['fuel'] or 'none'}",
            '  Stats: '+json.dumps(r['stats']), '  Repair: '+str(r['repair'])+'; upgrades '+str(r['upgrade_of']), '  Economy: '+r['economy'],'']
lines+=['RESOURCE ACQUISITION','']
for r in catalogue['resources']:lines += [r['id']+' - '+r['availability'],'  '+r['source'],'  Alternative: '+r['alternate']]
lines+=['','SUPPLY ROUTES AND FUTURE TARGETS (SEE EACH STATUS)',json.dumps(catalogue['deterministic_supply_targets'],indent=2),
        '','STATIONS AND KNOWLEDGE',json.dumps(stations,indent=2),json.dumps(knowledge,indent=2),
        '','FOREST GARDEN COORDINATES',json.dumps(gardens,indent=2)]
(ROOT/'docs/forest-crafting-catalogue.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'Catalogue: {len(rows)} recipe variants, {len(routes)} resources/products; {len(mapping)} live ownership mappings.')
