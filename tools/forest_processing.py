"""M2 production chains. Native workstation/collector/repair behavior, authored recipes."""
from pathlib import Path
from copy import deepcopy
from xml.etree import ElementTree as E
import json
ROOT=Path(__file__).resolve().parents[1]
STATIONS=[
 ('delveFieldHearth','Field Hearth','Cooking',1,{'resourceRockSmall':20,'resourceClayLump':10}),
 ('delveForgeAnvil','Forest Forge','Smithing',1,{'resourceRockSmall':40,'resourceClayLump':30,'resourceWood':20}),
 ('delveSawKit','Saw and Seasoning Bench','Carpentry',10,{'resourceForgedIron':4,'resourceWood':20}),
 ('delveOutfittingKit','Outfitting Bench','Carpentry',10,{'resourceWood':20,'resourceCloth':8,'resourceBone':4}),
 ('delveMortarKit','Apothecary Bench','Alchemy',10,{'resourceRockSmall':20,'resourceClayLump':10,'resourceWood':5}),
 ('delveSortingTable','Ore Sorting Table','Mining',10,{'resourceWood':20,'resourceRockSmall':20}),
 ('delveInscriptionKit','Rune Inscription Bench','Alchemy',10,{'resourceRockSmall':10,'resourceCloth':4,'resourceForgedIron':2}),
]
def station_windows(root,native):
    a=E.SubElement(root,'append',xpath='/xui')
    for name,*_ in STATIONS:
        g=deepcopy(native.find(".//window_group[@name='workstation_workbench']"));g.set('name','workstation_'+name);a.append(g)

def extend(base,blocks,items,recipes,buffs,node,prop,loc):
    ba=blocks.find("append[@xpath='/blocks']");ra=recipes.find("append[@xpath='/recipes']")
    manifest={'recipes':[],'stations':[],'repairs':{},'meal_items':[],'drink_items':[]}
    def recipe(name,inputs,skill='Carpentry',rank=1,count=1,station=None,seconds=20):
        r=node(ra,'recipe',name=name,count=count,craft_time=seconds)
        if station:r.set('craft_area',station)
        for k,v in inputs.items():node(r,'ingredient',name=k,count=v)
        manifest['recipes'].append(dict(name=name,skill=skill,rank=rank,count=count,ingredients=inputs,station=station or '',seconds=seconds))
    def item(name,title,desc,parent='resourceCloth',repair=None):
        it=node(items,'item',name=name)
        for k,v in {'Extends':parent,'CustomIcon':parent,'DescriptionKey':name+'Desc','UnlockedBy':'','CreativeMode':'Player','EconomicValue':0,'SellableToTrader':'false','Weight':0,'Stacknumber':100,'Tags':'delveProcessing'}.items():prop(it,k,v)
        if repair:prop(it,'RepairAmount',32000);prop(it,'RepairTime',3)
        loc(name,title);loc(name+'Desc',desc);return it
    for name,title,skill,rank,inputs in STATIONS:
        b=node(ba,'block',name=name)
        for k,v in {'Extends':'workbench','CustomIcon':'workbench','DescriptionKey':name+'Desc','UnlockedBy':'','EconomicValue':0,'SellableToTrader':'false','HeatMapStrength':0,'WorkstationWindow':'workstation_'+name,'WorkstationName':name}.items():prop(b,k,v)
        ws=node(b,'property',**{'class':'Workstation'});prop(ws,'Modules','output');prop(ws,'CraftingAreaRecipes',name)
        rp=node(b,'property',**{'class':'RepairItems'});prop(rp,'resourceWood',5)
        node(b,'dropextendsoff');node(b,'drop',event='Destroy',count=0)
        loc(name,title);loc(name+'Desc',f'{skill} {rank}. Place and interact. Native workbench appearance. Fuel is included in each heated recipe, not a separate fuel slot. No books or rare parts required.')
        recipe(name,inputs,skill,rank);manifest['stations'].append(dict(name=name,skill=skill,rank=rank))
    components=[
      ('delveRoughHandle','Rough Handle','Carpentry',1,None,{'resourceWood':6},2),
      ('delveLeatherBinding','Leather Binding','Carpentry',1,None,{'resourceLeather':2},4),
      ('delveSeasonedTimber','Seasoned Timber','Carpentry',10,'delveSawKit',{'resourceWood':12},4),
      ('delveCuredLeather','Cured Leather','Carpentry',10,'delveOutfittingKit',{'resourceLeather':4,'resourceWood':2},2),
      ('delveWovenCloth','Woven Cloth','Carpentry',10,'delveOutfittingKit',{'resourceCloth':4},2),
      ('delveIronFittings','Iron Fittings','Smithing',10,'delveForgeAnvil',{'resourceForgedIron':2,'delveCharcoal':1},4),
      ('delveDressedStone','Dressed Stone','Mining',10,'delveSortingTable',{'resourceRockSmall':10},4),
      ('delveIronConcentrate','Iron Concentrate','Mining',20,'delveSortingTable',{'resourceScrapIron':20},1),
      ('delveHerbalExtract','Herbal Extract','Alchemy',10,'delveMortarKit',{'resourceDelveYarrow':2,'resourceDelveThyme':1},2),
      ('delveRuneBlank','Rune Blank','Mining',10,'delveSortingTable',{'resourceRockSmall':5},10),
      ('delveCharcoal','Charcoal','Smithing',1,'delveFieldHearth',{'resourceWood':10},5),
      ('delveHideRepair','Hide Repair Supplies','Carpentry',1,None,{'resourceLeather':2,'resourceCloth':2},2),
      ('delveMetalRepair','Metal Repair Supplies','Smithing',1,None,{'resourceScrapIron':10,'resourceCloth':2},2),
      ('delveFocusRepair','Focus Repair Supplies','Carpentry',1,None,{'resourceWood':5,'resourceCloth':2},2),
    ]
    for name,title,skill,rank,station,inputs,count in components:
        item(name,title,f'{skill} {rank}. Forest processing supply. '+('Repairs matching Delve equipment to full durability.' if name.endswith('Repair') else 'Used in Forest processing recipes.'),repair=name.endswith('Repair'))
        recipe(name,inputs,skill,rank,count,station)
    # Distinct station variants preserve native recipes and avoid knowledge/smelting deadlocks.
    for name,inputs,skill,rank,count,station,seconds in [
      ('resourceForgedIron',{'resourceScrapIron':20,'resourceClayLump':2,'delveCharcoal':1},'Smithing',1,1,'delveForgeAnvil',30),
      ('resourceForgedIron',{'delveIronConcentrate':1,'resourceClayLump':2,'delveCharcoal':1},'Smithing',1,2,'delveForgeAnvil',30),
      ('resourceCloth',{'resourceYuccaFibers':10},'Carpentry',1,1,None,10),
      ('resourceGlue',{'resourceBone':3,'drinkJarBoiledWater':1},'Alchemy',1,1,'delveFieldHearth',20),
      ('resourceLeather',{'resourceYuccaFibers':20,'delveHerbalExtract':1},'Carpentry',1,2,'delveOutfittingKit',30),
      ('toolCookingPot',{'resourceScrapIron':20,'delveCharcoal':2},'Smithing',1,1,'delveForgeAnvil',30),
      ('drinkJarEmpty',{'resourceClayLump':2,'delveCharcoal':1},'Cooking',1,1,'delveFieldHearth',15),
      ('drinkJarBoiledWater',{'drinkJarRiverWater':1,'delveCharcoal':1},'Cooking',1,1,'delveFieldHearth',20),
      ('delveEmberSalts',{'resourceDelveMooncap':2,'delveCharcoal':1},'Alchemy',1,2,'delveMortarKit',20),
      ('medicalBandage',{'delveWovenCloth':1},'Alchemy',1,3,'delveOutfittingKit',10),
      ('resourceRepairKit',{'resourceForgedIron':1,'resourceCloth':2,'resourceGlue':1},'Smithing',1,1,'delveForgeAnvil',20),
      ('delveFocusRepair',{'delveSeasonedTimber':1,'delveWovenCloth':1},'Carpentry',1,3,'delveSawKit',10),
      ('delveHideRepair',{'delveCuredLeather':1,'delveWovenCloth':1},'Carpentry',1,3,'delveOutfittingKit',10),
      ('resourceCobblestones',{'delveDressedStone':2,'resourceClayLump':2},'Mining',1,12,'delveSortingTable',10),
    ]:recipe(name,inputs,skill,rank,count,station,seconds)
    for name in ['delveWandRune','delveStaffRune','delveTotemRune','delveHealingRune']:
        recipe(name,{'delveRuneBlank':10,'delveHerbalExtract':1,'delveEmberSalts':1},'Alchemy',1,10,'delveInscriptionKit')
    recipe('delveArborProtection',{'drinkJarBoiledWater':1,'delveEmberSalts':3,'resourceDelveYarrow':2},'Alchemy',20,1,'delveMortarKit',30)
    # Collector uses native jar-fuel production, sky exposure and saved tile-entity state.
    b=node(ba,'block',name='delveRainCollector')
    for k,v in {'Extends':'cntDewCollector','CustomIcon':'cntDewCollector','UnlockedBy':'','DescriptionKey':'delveRainCollectorDesc','OutputTypes':'{water,jar,1,1,1,drinkJarRiverWater,drinkJarBoiledWater,2,2,500,1000,collector_complete_item}','EconomicValue':0,'SellableToTrader':'false'}.items():prop(b,k,v)
    rp=node(b,'property',**{'class':'RepairItems'});prop(rp,'resourceWood',5)
    node(b,'dropextendsoff');node(b,'drop',event='Destroy',count=0)
    loc('delveRainCollector','Forest Rain Collector');loc('delveRainCollectorDesc','Place outdoors with open sky. Insert empty jars (craft from clay and charcoal at a Field Hearth). Collect murky water after 0.5–1 game hour per slot; boil it at the hearth. Native collector upgrades remain optional.')
    recipe('delveRainCollector',{'resourceWood':40,'resourceCloth':10,'resourceRockSmall':20})
    # Repairs are real native RepairTools bindings, not decorative inventory items.
    for it in list(items):
        name=it.get('name','')
        if name.startswith('armorDelve'):supply='delveMetalRepair' if 'Heavy' in name else 'delveHideRepair'
        elif name in ['delveBoneDagger','delveIronDagger','delveIronMace','delveIronSpear']:supply='delveMetalRepair'
        elif name in ['delveLeatherKnuckles']:supply='delveHideRepair'
        elif name in ['delveOakCudgel','delveAshSpear','delveBorderBow','delveHuntingBow','delveStarterWand','delveStarterStaff','delveStarterTotem','delveMendingTotem']:supply='delveFocusRepair'
        else:continue
        old=it.find("property[@name='RepairTools']")
        if old is not None:old.set('value',supply)
        else:prop(it,'RepairTools',supply)
        manifest['repairs'][name]=supply
    for name,title,inputs,hunger,water in [
      ('foodDelveTrailRations','Forest Trail Rations',{'foodRawMeat':2,'foodDelveBrambleberries':2},25,0),
      ('foodDelveGathererPorridge','Gatherer Porridge',{'foodCornMeal':2,'drinkJarBoiledWater':1,'resourceDelveThyme':1},30,10),
      ('foodDelveIncursionSupper','Incursion Supper',{'foodRawMeat':2,'foodCropPotato':2,'drinkJarBoiledWater':1,'resourceDelveThyme':1},40,15),
    ]:
        it=item(name,title,'Forest provision. Cook at a Field Hearth.',parent='foodCornBread')
        eg=node(it,'effect_group',tiered='false')
        for cvar,amount in [('$foodAmountAdd',hunger),('$waterAmountAdd',water)]:
            if amount:node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='ModifyCVar',cvar=cvar,operation='add',value=amount)
        node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='buffProcessConsumables')
        recipe(name,dict(inputs,delveCharcoal=1),'Cooking',20,1,'delveFieldHearth',30)
    # Existing food/restorative values stay intact; timed prepared-food bonuses replace.
    for category,stat,amount in [('Meal','StaminaMax',10),('Drink','StaminaChangeOT',.1)]:
        buff='delveForest'+category
        b=node(buffs,'buff',name=buff,name_key=buff,description_key=buff+'Desc',icon='ui_game_symbol_food' if category=='Meal' else 'ui_game_symbol_water')
        node(b,'stack_type',value='replace');node(b,'duration',value=900)
        eg=node(b,'effect_group');node(eg,'passive_effect',name=stat,operation='base_add' if category=='Meal' else 'perc_add',value=amount)
        loc(buff,'Forest '+category);loc(buff+'Desc',f'15 minutes. '+('Maximum stamina +10.' if category=='Meal' else 'Stamina regeneration +10%.')+' Replaces the previous Forest '+category.lower()+' bonus.')
    for it in items:
        name=it.get('name','');category='Meal' if name.startswith('foodDelve') and name!='foodDelveBrambleberries' else 'Drink' if name.startswith('drinkDelve') or name=='delveWayfarerTea' else None
        if category is None:continue
        for eg in it.findall('effect_group'):
            for fx in list(eg):
                if fx.get('cvar')=='.foodStaminaBonusAdd':eg.remove(fx)
        eg=node(it,'effect_group',tiered='false')
        node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='delveForest'+category)
        manifest['meal_items' if category=='Meal' else 'drink_items'].append(name)
        key=name+'Desc';loc(key,('Prepared Forest meal: +10 maximum stamina' if category=='Meal' else 'Prepared Forest drink: +10% stamina regeneration')+' for 15 minutes. One meal and one drink bonus can coexist; repeated servings refresh rather than stack. Food/water restoration is immediate through native digestion.')
    item('delveProcessingGuide','Forest Processing Guide','Gather wood, grass, stone, clay and iron in the Forest. Craft a Field Hearth, Forest Forge and Rain Collector. Make charcoal, jars and cloth, collect and boil water. At skill 10, build processing benches. Herbs and cotton grow from replanted seeds; hunting provides hides/bone, with a plant-based leather route at the outfitting bench. Repair matching gear with Focus/Hide/Metal supplies. Native tools use repair kits. Use the campfire for meals; the hearth needs no cooking pot. Read the release guide for recipes.',parent='resourcePaper')
    recipe('delveProcessingGuide',{'resourceYuccaFibers':1},skill=None)
    (ROOT/'src/Forest/processing.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows=['// Generated by forest_processing.py','namespace Delve { public static class ForestProcessingCatalog {']
    for method,key,typ,default in [('Skill','skill','string','null'),('Rank','rank','int','0')]:
        rows+=['public static '+typ+' '+method+'(string name) { switch((name ?? "").ToLowerInvariant()) {']
        for name in sorted({r['name'] for r in manifest['recipes']}):
            matches=[r for r in manifest['recipes'] if r['name']==name]; value=matches[0][key]
            assert all(r[key]==value for r in matches),(name,key)
            rows+=['case '+json.dumps(name.lower())+': return '+(json.dumps(value) if value is not None else 'null')+';']
        rows+=['default:return '+default+'; } }']
    rows+=['} }'];(ROOT/'src/Code/ForestProcessingCatalog.generated.cs').write_text('\n'.join(rows))

