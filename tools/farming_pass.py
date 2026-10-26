"""First farming production loop. Character milestones are distinct from proficiency."""
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as E
import json
import re

ROOT = Path(__file__).resolve().parents[1]
STATIONS = [
    ('delveFarmDispatch', 'Settlement Supply Desk', 1, {'resourceWood':20,'resourceYuccaFibers':10}),
    ('delveCompostBin', 'Compost Bin', 6, {'resourceWood':25,'resourceClayLump':10}),
    ('delveDryingRack', 'Herb Drying Rack', 6, {'resourceWood':20,'resourceYuccaFibers':15}),
    ('delveGrainMill', 'Hand Grain Mill', 11, {'resourceWood':30,'resourceRockSmall':40}),
    ('delvePreservingCrock', 'Preserving Crock', 16, {'resourceClayLump':40,'resourceRockSmall':10}),
    ('delveFermentingBarrel', 'Fermentation Barrel', 16, {'resourceWood':40,'resourceScrapIron':10}),
]


def station_windows(root, native):
    append=E.SubElement(root,'append',xpath='/xui')
    for name,_,_,_ in STATIONS:
        group=deepcopy(native.find(".//window_group[@name='workstation_workbench']"))
        group.set('name','workstation_'+name)
        append.append(group)


def extend(base, blocks, items, recipes, quests, entities, node, prop, loc):
    ba=blocks.find("append[@xpath='/blocks']")
    ra=recipes.find("append[@xpath='/recipes']")
    qa=quests.find("append[@xpath='/quests']")
    native_blocks=E.parse(base/'blocks.xml')
    native_recipes=E.parse(base/'recipes.xml')
    manifest={'recipes':[], 'stations':[], 'seeds':[], 'orders':[]}
    descriptions={}

    def register(name, level, skill, count, ingredients, station):
        rank=21 if name=='plantedAloe1' else (1 if level==1 or skill is None else 10 if level<=11 else 20)
        manifest['recipes'].append(dict(name=name,level=level,rank=rank,skill=skill,count=count,ingredients=ingredients,station=station or ''))

    def recipe(name, ingredients, level=1, skill='Farming', count=1, station=None, seconds=15):
        r=node(ra,'recipe',name=name,count=count,craft_time=seconds)
        if station:r.set('craft_area',station)
        for key,value in ingredients.items():node(r,'ingredient',name=key,count=value)
        register(name,level,skill,count,ingredients,station)
        return r

    def item(name, title, desc, parent='resourceCloth', icon=None):
        it=node(items,'item',name=name)
        for key,value in {'Extends':parent,'CustomIcon':icon or parent,'DescriptionKey':name+'Desc',
                          'CreativeMode':'Player','UnlockedBy':'','EconomicValue':'1','Stacknumber':'100'}.items():prop(it,key,value)
        loc(name,title);loc(name+'Desc',desc)
        descriptions[name]=desc
        return it

    # Cultivated harvests always return the planting seed. Wild acquisition is unchanged.
    for crop in ['Corn','Potato','Pumpkin','Mushroom','Blueberry','Cotton','Chrysanthemum','Goldenrod','Aloe']:
        seed='planted'+crop+'1'; ripe='planted'+crop+'3HarvestPlayer'
        b=native_blocks.find(f"block[@name='{ripe}']")
        assert b.find(f"drop[@event='Destroy'][@name='{seed}']") is not None
        node(blocks,'set',xpath=f"/blocks/block[@name='{ripe}']/drop[@event='Destroy'][@name='{seed}']/@prob").text='1'
        r=native_recipes.find(f"recipe[@name='{seed}']")
        ingredient=r.find('ingredient').get('name')
        node(recipes,'set',xpath=f"/recipes/recipe[@name='{seed}']/ingredient[@name='{ingredient}']/@count").text='2'
        node(recipes,'set',xpath=f"/recipes/recipe[@name='{seed}']/@tags").text='packMuleCrafting'
        node(blocks,'remove',xpath=f"/blocks/block[@name='{seed}']/property[@name='UnlockedBy']")
        ingredients={i.get('name'):int(i.get('count')) for i in r.findall('ingredient')}
        ingredients[ingredient]=2
        register(seed,1,'Farming',1,ingredients,None)
        manifest['seeds'].append(dict(seed=seed,ripe=ripe,ingredient=ingredient))

    # Reuse the working vanilla workstation, including its footprint and interaction.
    # Each has its own recipe area and UI group; inherited salvage is explicitly cleared.
    for name,title,level,ingredients in STATIONS:
        b=node(ba,'block',name=name)
        for key,value in {'Extends':'workbench','CustomIcon':'workbench','DescriptionKey':name+'Desc',
                          'UnlockedBy':'','EconomicValue':'20','HeatMapStrength':'0',
                          'WorkstationWindow':'workstation_'+name,'WorkstationName':name}.items():prop(b,key,value)
        workstation=node(b,'property',**{'class':'Workstation'})
        prop(workstation,'Modules','output');prop(workstation,'CraftingAreaRecipes',name)
        repair=node(b,'property',**{'class':'RepairItems'})
        prop(repair,'resourceWood',5)
        node(b,'dropextendsoff');node(b,'drop',event='Destroy',count=0)
        loc(name,title)
        loc(name+'Desc',f'Character level {level}. Place and interact to process supplies. Uses a workbench model in this first pass. No fuel required; collect finished goods from its output slots.')
        descriptions[name]='Place and interact to process supplies. Temporary workbench model. No fuel required.'
        recipe(name,ingredients,level,'Carpentry',seconds=20)
        manifest['stations'].append(dict(name=name,level=level))

    item('delveCompost','Mature Compost','Character level 6. Compost plant fibers and rotten flesh in a Compost Bin. Used to make inexpensive farm plots; does not apply a growth buff.',icon='foodRottingFlesh')
    recipe('delveCompost',{'resourceYuccaFibers':10,'foodRottingFlesh':2},6,station='delveCompostBin',count=2,seconds=120)
    b=node(ba,'block',name='delveCompostedFarmPlot')
    prop(b,'Extends','farmPlotBlockVariantHelper');prop(b,'CustomIcon','farmPlotBlock')
    prop(b,'DescriptionKey','delveCompostedFarmPlotDesc')
    loc('delveCompostedFarmPlot','Compost Farm Plot Shapes')
    loc('delveCompostedFarmPlotDesc','Character level 6. Farm plot shapes made with compost instead of nitrate. Includes the borderless plate. Breaking a placed plot returns the standard Farm Plot item.')
    recipe('delveCompostedFarmPlot',{'resourceClayLump':10,'resourceWood':2,'delveCompost':1},6)

    for name,title,raw in [('delveDriedThyme','Dried Thyme','resourceDelveThyme'),('delveDriedYarrow','Dried Yarrow','resourceDelveYarrow')]:
        icon='resourceCropChrysanthemumPlant' if raw=='resourceDelveThyme' else 'resourceCropGoldenrodPlant'
        item(name,title,'Character level 6. Dry herbs at a Herb Drying Rack. Used in prepared meals, medicine and settlement orders.',icon=icon)
        recipe(name,{raw:2},6,skill='Alchemy',station='delveDryingRack',seconds=45)
    item('delveMilledGrain','Milled Grain','Character level 11. Mill corn into grain for travel bread and preserves.',icon='foodCornMeal')
    recipe('delveMilledGrain',{'foodCropCorn':2},11,'Cooking',count=2,station='delveGrainMill',seconds=30)
    item('delveHerbalSpirit','Herbal Spirit','Character level 16. A fermented alchemical solvent; not a drink. Used in tinctures and infirmary supplies.',icon='drinkJarBeer')
    recipe('delveHerbalSpirit',{'foodDelveBrambleberries':4,'drinkJarBoiledWater':1},16,'Alchemy',station='delveFermentingBarrel',seconds=180)

    def food(name,title,ingredients,level,hunger,water,station):
        it=item(name,title,f'Character level {level}. Restores {hunger} food and {water} water. Made at '+dict((s[0],s[1]) for s in STATIONS).get(station,'a campfire')+'.',parent='foodCornBread')
        eg=node(it,'effect_group',tiered='false')
        for cvar,amount in [('$foodAmountAdd',hunger),('$waterAmountAdd',water)]:
            if amount:node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='ModifyCVar',cvar=cvar,operation='add',value=amount)
        node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='buffProcessConsumables')
        recipe(name,ingredients,level,'Cooking',station=station,seconds=30)

    food('foodDelveTravelBread','Herbed Travel Bread',{'delveMilledGrain':2,'delveDriedThyme':1,'drinkJarBoiledWater':1},11,28,0,'campfire')
    food('foodDelveBerryPreserve','Bramble Preserve',{'foodDelveBrambleberries':4,'drinkJarBoiledWater':1},16,24,5,'delvePreservingCrock')
    food('foodDelveTrailRation','Harvest Trail Ration',{'foodDelveTravelBread':1,'foodDelveBerryPreserve':1},16,55,5,'delvePreservingCrock')
    it=item('medicalDelveYarrowTincture','Yarrow Tincture','Character level 16. Restores 35 health over time and stops bleeding. Made from dried yarrow and fermented herbal spirit.',parent='medicalFirstAidBandage')
    eg=node(it,'effect_group',tiered='false')
    for trigger,target in [('onSelfPrimaryActionEnd','self'),('onSelfSecondaryActionEnd','other')]:
        node(eg,'triggered_effect',trigger=trigger,action='ModifyCVar',target=target,cvar='medicalRegHealthAmount',operation='add',value=35)
        node(eg,'triggered_effect',trigger=trigger,action='ModifyCVar',target=target,cvar='medRegHealthIncSpeed',operation='set',value=2)
        node(eg,'triggered_effect',trigger=trigger,action='AddBuff',target=target,buff='buffProcessConsumables')
        node(eg,'triggered_effect',trigger=trigger,action='RemoveBuff',target=target,buff='buffInjuryBleeding')
    recipe('medicalDelveYarrowTincture',{'delveDriedYarrow':2,'delveHerbalSpirit':1,'resourceCloth':1},16,'Alchemy',station='delveFermentingBarrel',seconds=45)

    # Pack goods at the desk, then the native Fetch objective consumes the sealed
    # parcel. A single consuming objective avoids reusing ingredients across orders.
    orders=[('Pantry','Wayrest Pantry',1,{'foodCropCorn':6,'foodCropPotato':4},60),
            ('Herbs','Wayrest Infirmary: Dried Herbs',6,{'delveDriedYarrow':3,'delveDriedThyme':2},90),
            ('Bread','Wayrest Guard: Bread Supply',11,{'foodDelveTravelBread':4},140),
            ('Medicine','Wayrest Infirmary: Tinctures',16,{'medicalDelveYarrowTincture':3},180),
            ('Rations','Wayrest Expedition: Rations',20,{'foodDelveTrailRation':4},240)]
    loc('delveFarmOrderCategory','Allium: Settlement Supplies')
    for key,title,level,ingredients,gold in orders:
        quest='delveFarmOrder'+key; notice='delveFarmNotice'+key; parcel='delveFarmParcel'+key
        desc=f'Character level {level}. Read this order, then pack its supplies at a Settlement Supply Desk. The sealed parcel is consumed automatically on delivery. Reward: {gold} gold. Repeatable; no talent points.'
        it=item(notice,'Supply Order: '+title,desc,parent='questMaster',icon='resourcePaper')
        action=node(it,'property',**{'class':'Action0'});prop(action,'Class','Quest');prop(action,'QuestGiven',quest)
        node(action,'requirement',name='PlayerLevel',operation='GTE',value=level)
        recipe(notice,{'resourceYuccaFibers':1},level,None,station='delveFarmDispatch',seconds=1)
        item(parcel,'Sealed Supplies: '+title,'Packed settlement goods. Consumed by the matching active supply order. Read that order to receive payment.',icon='resourceWood')
        recipe(parcel,ingredients,level,None,station='delveFarmDispatch',seconds=10)
        q=node(qa,'quest',id=quest)
        loc(quest,title);loc(quest+'Desc',desc)
        for k,v in {'name_key':quest,'subtitle_key':quest,'description_key':quest+'Desc','offer_key':quest+'Desc',
                    'icon':'ui_game_symbol_hammer','category_key':'delveFarmOrderCategory','repeatable':'true',
                    'shareable':'false','add_to_tier_complete':'false','completiontype':'AutoComplete'}.items():prop(q,k,v)
        node(q,'objective',type='Fetch',id=parcel,value=1,phase=1)
        node(q,'reward',type='Item',id='casinoCoin',value=gold)
        manifest['orders'].append(dict(quest=quest,notice=notice,parcel=parcel,level=level,gold=gold))

    guide=item('delveFarmHandbook','Farming: First Harvest',
        'READ once to begin farming. Crafting proficiency 1: sustainable Forest seeds and a supply desk. Proficiency 10 in the owning craft: compost, dried herbs, milling and travel bread. Proficiency 20: preserves, fermentation and tinctures. Supply order acceptance retains character-level milestones. Harvest ripe crops to recover seeds. Aloe belongs to the later desert tier.',parent='questMaster',icon='resourcePaper')
    action=node(guide,'property',**{'class':'Action0'});prop(action,'Class','Quest');prop(action,'QuestGiven','delveFarmFirstHarvest')
    recipe('delveFarmHandbook',{'resourceYuccaFibers':1},skill=None)
    q=node(qa,'quest',id='delveFarmFirstHarvest')
    loc('delveFarmFirstHarvest','First Harvest');loc('delveFarmFirstHarvestDesc','Gather five plant fibers to claim your one-time starter seeds. Craft farm plots, plant the seeds, and harvest only when fully grown. Every ripe cultivated starter crop returns a seed. Craft a Settlement Supply Desk to accept and pack orders.')
    for k,v in {'name_key':'delveFarmFirstHarvest','description_key':'delveFarmFirstHarvestDesc','offer_key':'delveFarmFirstHarvestDesc',
                'category_key':'delveFarmOrderCategory','icon':'ui_game_symbol_hammer','repeatable':'false','shareable':'false','completiontype':'AutoComplete'}.items():prop(q,k,v)
    node(q,'objective',type='Fetch',id='resourceYuccaFibers',value=5,phase=1)
    for seed in ['plantedCorn1','plantedChrysanthemum1']:node(q,'reward',type='Item',id=seed,value=3)
    for op in entities.findall('set'):
        if 'ItemsOnEnterGame' in op.get('xpath',''):op.text+=',delveFarmHandbook'

    for row in manifest['recipes']:
        if row['skill'] and row['name'] in descriptions:
            desc=re.sub(r'Character level \d+\.\s*','',descriptions[row['name']])
            loc(row['name']+'Desc',f"{row['skill']} proficiency {row['rank']}. "+desc)
    target=ROOT/'src/Farming';target.mkdir(exist_ok=True)
    (target/'first-pass.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    rows=['// Generated by farming_pass.py','namespace Delve { public static class FarmingCatalog {',
          'public static int Level(string name) { switch((name ?? "").ToLowerInvariant()) {']
    for r in manifest['recipes']:rows.append(f'case "{r["name"].lower()}": return {r["level"]};')
    rows+=['default:return 0; } }','public static int Rank(string name) { switch((name ?? "").ToLowerInvariant()) {']
    for r in manifest['recipes']:rows.append(f'case "{r["name"].lower()}": return {r["rank"]};')
    rows+=['default:return 0; } }','public static string Skill(string name) { switch((name ?? "").ToLowerInvariant()) {']
    for r in manifest['recipes']:rows.append(f'case "{r["name"].lower()}": return '+('"'+r['skill']+'"' if r['skill'] else 'null')+';')
    rows+=['default:return null; } } } }']
    (ROOT/'src/Code/FarmingCatalog.generated.cs').write_text('\n'.join(rows)+'\n',encoding='utf-8')
