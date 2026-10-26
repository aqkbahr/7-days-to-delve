"""Early forest food, medicine and renewable biome plant acquisition."""
from copy import deepcopy
from xml.etree import ElementTree as E
from pathlib import Path
import json

PLANTS = [
    ('Bramble', 'Brambleberries', 'Blueberry', 'foodCropBlueberries', 'foodDelveBrambleberries', 'b84265'),
    ('Yarrow', 'Yarrow', 'Goldenrod', 'resourceCropGoldenrodPlant', 'resourceDelveYarrow', 'eee6ce'),
    ('Thyme', 'Wild Thyme', 'Chrysanthemum', 'resourceCropChrysanthemumPlant', 'resourceDelveThyme', 'ad87bb'),
    ('Mooncap', 'Mooncaps', 'Mushroom', 'foodCropMushrooms', 'resourceDelveMooncap', '8fcbe8'),
]

def extend(base, blocks, items, recipes, buffs, node, prop, loc):
    native_blocks = E.parse(base/'blocks.xml')
    native_items = E.parse(base/'items.xml')
    ba = blocks.find("append[@xpath='/blocks']")
    ra = recipes.find("append[@xpath='/recipes']")
    manifest = {'plants': [], 'recipes': [], 'biomes': {}}

    def recipe(name, ingredients, rank=1, skill='Cooking', count=1, station=None):
        r = node(ra, 'recipe', name=name, count=count, craft_time=10)
        if station: r.set('craft_area', station)
        for ingredient, quantity in ingredients.items(): node(r, 'ingredient', name=ingredient, count=quantity)
        manifest['recipes'].append(dict(name=name, skill=skill, rank=rank, count=count, ingredients=ingredients))
        return r

    def item(name, parent, title, desc, tint=None):
        assert native_items.find(f"item[@name='{parent}']") is not None, parent
        it = node(items, 'item', name=name)
        for k,v in {'Extends':parent, 'CustomIcon':parent, 'CreativeMode':'Player', 'UnlockedBy':'',
                    'DescriptionKey':name+'Desc', 'EconomicValue':1}.items(): prop(it,k,v)
        if tint: prop(it,'CustomIconTint',tint)
        loc(name,title); loc(name+'Desc',desc)
        return it

    for key,title,source,raw,output,tint in PLANTS:
        item(output, raw, title, 'Forest ingredient. Gather wild plants or cultivate seeds on a Farm Plot. Native plant visuals are temporary.', tint)
        prefix = 'plantedDelve'+key
        for suffix in ('1','2','3Harvest','3HarvestPlayer'):
            original = native_blocks.find(f"block[@name='planted{source}{suffix}']")
            b = deepcopy(original); b.set('name',prefix+suffix)
            for p in b.iter('property'):
                value=p.get('value','')
                if p.get('name') in ('Extends','Next') and value.startswith('planted'+source):
                    p.set('value',value.replace('planted'+source,prefix))
                if p.get('name')=='UnlockedBy': p.set('value','')
            for d in list(b.findall('drop')): b.remove(d)
            node(b,'dropextendsoff')
            if suffix in ('1','2'):
                node(b,'drop',event='Destroy',name=prefix+'1',count=1)
            else:
                E.SubElement(b,'drop',event='Harvest',name=output,count='2' if suffix.endswith('Player') else '1',
                     tag='cropHarvest' if suffix.endswith('Player') else 'wildCropsHarvest')
                node(b,'drop',event='Destroy',name=prefix+'1',count=1,prob=1 if suffix.endswith('Player') else .25)
            # Clear inherited vanilla descriptions/icons; preserve native growth/model properties.
            for pname,pvalue in [('CustomIcon','planted'+source+'1'),('CustomIconTint',tint),('DescriptionKey',prefix+'Desc')]:
                existing=b.find(f"property[@name='{pname}']")
                if existing is not None: existing.set('value',pvalue)
                else: prop(b,pname,pvalue)
            ba.append(b)
            loc(prefix+suffix, title+(' Seeds' if suffix=='1' else ' (Growing)' if suffix=='2' else ' (Ripe)'))
        loc(prefix+'Desc','Plant on a Farm Plot. Two growth stages, about 126 real minutes total. Ripe cultivated plants return two ingredients and one seed; wild plants have a 25% seed chance.')
        recipe(prefix+'1',{output:2},skill='Farming')
        manifest['plants'].append(dict(key=key, item=output, seed=prefix+'1', wild=prefix+'3Harvest', cultivated=prefix+'3HarvestPlayer'))

    def food(name,title,ingredients,hunger,water=0,health=0,stamina=0,rank=1,drink=False,count=1,stack=10):
        parent='drinkJarRedTea' if drink else 'foodCornBread'
        it=item(name,parent,title,f'Cooking {rank}. Restores {hunger} food, {water} water and {health} health. Food stamina bonus: {stamina}. Cook at a campfire.')
        prop(it,'Stacknumber',stack)
        eg=node(it,'effect_group',tiered='false')
        for cvar,value in [('$foodAmountAdd',hunger),('$waterAmountAdd',water),('foodHealthAmount',health),('.foodStaminaBonusAdd',stamina)]:
            if value: node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='ModifyCVar',cvar=cvar,operation='add',value=value)
        node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='buffProcessConsumables')
        recipe(name,ingredients,rank,count=count,station='campfire')

    berries='foodDelveBrambleberries'; thyme='resourceDelveThyme'; yarrow='resourceDelveYarrow'
    water='drinkJarBoiledWater'; corn='foodCornMeal'; mushrooms='foodCropMushrooms'; honey='foodHoney'
    food('foodDelveCookedBerries','Cooked Berries',{berries:3},8)
    food('foodDelveMushroomSkewers','Mushroom Skewers',{mushrooms:3},10)
    food('foodDelveCornPorridge','Corn Porridge',{corn:1,water:1},12,5)
    food('foodDelveRoastedPumpkin','Roasted Pumpkin',{'foodCropPumpkin':2},12)
    food('foodDelveSeasonedRoast','Seasoned Roast',{'foodRawMeat':3,thyme:1},20,health=3,stamina=10,rank=10)
    food('drinkDelveWoodlandBroth','Woodland Broth',{mushrooms:2,thyme:1,water:1},5,15,rank=10,drink=True)
    food('foodDelveBerryPorridge','Berry Porridge',{corn:1,berries:2,water:1},20,5,stamina=10,rank=10)
    food('foodDelveHunterStew',"Hunter's Stew",{'foodRawMeat':2,'foodCropPotato':1,'drinkDelveWoodlandBroth':1},35,10,5,20,rank=20)
    food('foodDelveHoneyberryCakes','Honeyberry Cakes',{corn:2,berries:2,honey:1},18,stamina=10,rank=20,count=2,stack=20)
    food('drinkDelveGoldenrodTea','Border Goldenrod Tea',{'resourceCropGoldenrodPlant':2,water:1},0,24,drink=True)

    for name,title,ingredients,amount,rank in [
        ('medicalDelveFieldPoultice','Field Poultice',{yarrow:2,'resourceYuccaFibers':4},10,1),
        ('medicalDelveHerbalDressing','Herbal Dressing',{'medicalBandage':1,yarrow:2,honey:1},35,20),
    ]:
        it=item(name,'medicalFirstAidBandage',title,f'Alchemy {rank}. Restores {amount} health over time and stops bleeding. Apply to yourself or an ally.')
        eg=node(it,'effect_group',tiered='false')
        for trigger,target in [('onSelfPrimaryActionEnd','self'),('onSelfSecondaryActionEnd','other')]:
            node(eg,'triggered_effect',trigger=trigger,action='ModifyCVar',target=target,cvar='medicalRegHealthAmount',operation='add',value=amount)
            node(eg,'triggered_effect',trigger=trigger,action='ModifyCVar',target=target,cvar='medRegHealthIncSpeed',operation='set',value=2)
            node(eg,'triggered_effect',trigger=trigger,action='AddBuff',target=target,buff='buffProcessConsumables')
            node(eg,'triggered_effect',trigger=trigger,action='RemoveBuff',target=target,buff='buffInjuryBleeding')
        node(eg,'display_value',name='foodHealthAmount',value=amount)
        recipe(name,ingredients,rank,'Alchemy')

    cooldown=node(buffs,'buff',name='delveRestorativeCooldown',hidden='true')
    node(cooldown,'stack_type',value='replace');node(cooldown,'duration',value=20)
    for kind,ingredients,stat,amount in [('Healing',{'resourceCropChrysanthemumPlant':2,yarrow:2,water:1},'Health',25),
                                         ('Stamina',{'resourceCropGoldenrodPlant':2,berries:2,water:1},'Stamina',40)]:
        name='delveLesser'+kind+'Potion'
        it=item(name,'drinkJarRedTea','Lesser '+kind+' Potion',f'Alchemy 20. Restores {amount} {stat.lower()} immediately. Healing and stamina potions share a 20-second cooldown.')
        ac=node(it,'property',**{'class':'Action0'})
        node(ac,'requirement',name='!HasBuff',buff='delveRestorativeCooldown')
        node(ac,'requirement',name='StatComparePercCurrentToMax',stat=stat,operation='LT',value=1)
        eg=node(it,'effect_group',tiered='false')
        node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='ModifyStats',stat=stat,operation='add',value=amount)
        node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='delveRestorativeCooldown')
        recipe(name,ingredients,20,'Alchemy',station='campfire')

    # Native bandages and cornmeal are deliberately available at the start.
    for name,ingredients in [('medicalBandage',{'resourceCloth':2}),('foodCornMeal',{'foodCropCorn':2})]:
        for ingredient,count in ingredients.items():
            node(recipes,'set',xpath=f"/recipes/recipe[@name='{name}']/ingredient[@name='{ingredient}']/@count").text=str(count)
    # Alternate recipe names must use recipe tags for the engine's output lookup;
    # use distinct rune items compatible with existing ammo lists instead (below).
    for kind in ('Wand','Staff','Totem','Healing'):
        name='delveMooncap'+kind+'Rune'; original='delve'+kind+'Rune'
        source=items.find(f"item[@name='{original}']")
        assert source is not None,original
        it=deepcopy(source);it.set('name',name)
        p=it.find("property[@name='DescriptionKey']");p.set('value',name+'Desc')
        items.append(it);loc(name,'Mooncap '+kind+' Runes');loc(name+'Desc','Alchemy 20. Efficient forest-grown ammunition; same payload as the basic rune.')
        recipe(name,{'resourceRockSmall':5,'resourceDelveMooncap':1},20,'Alchemy',count=20)
        for ammo in items.findall(".//property[@name='Magazine_items']"):
            choices=ammo.get('value').split(',')
            if original in choices: ammo.set('value',ammo.get('value')+','+name)

    assignments={
        'pine_forest':['Corn','Potato','Pumpkin','Mushroom','Blueberry','Cotton','Chrysanthemum','Goldenrod','DelveBramble','DelveYarrow','DelveThyme','DelveMooncap'],
        'burnt_forest':['Coffee','Hop','Mushroom'],
        'desert':['Aloe','Yucca'], 'snow':['Snowberry','Blueberry'], 'wasteland':['GraceCorn'],
    }
    biomes=E.Element('configs'); native_biomes=E.parse(base/'biomes.xml')
    seeded=set()
    for biome,crops in assignments.items():
        manifest['biomes'][biome]=[]
        for crop in crops:
            block='planted'+crop+'3Harvest'
            assert native_blocks.find(f"block[@name='{block}']") is not None or crop.startswith('Delve'),block
            rate=.0004 if crop in ('GraceCorn','DelveMooncap') else .002
            manifest['biomes'][biome].append(dict(block=block,prob=rate))
            for i,deco in enumerate(native_biomes.findall(f"biomes/biome[@name='{biome}']//decorations"),1):
                if deco.find(f"decoration[@blockname='{block}']") is not None: continue
                a=node(biomes,'append',xpath=f"(/worldgeneration/biomes/biome[@name='{biome}']//decorations)[{i}]")
                node(a,'decoration',type='block',blockname=block,prob=rate,rotatemax=3)
            # Every wild crop can yield a seed; cultivated vanilla behavior stays intact.
            if not crop.startswith('Delve') and crop not in seeded:
                seeded.add(crop)
                b=native_blocks.find(f"block[@name='{block}']")
                seed='planted'+crop+'1'
                if not b.findall(f"drop[@name='{seed}']"):
                    a=node(blocks,'append',xpath=f"/blocks/block[@name='{block}']")
                    node(a,'drop',event='Destroy',name=seed,count=1,prob=.25)
    # Explicit recipe ownership and gates are generated from the same data.
    root=Path(__file__).resolve().parents[1]
    (root/'src/Forest/pantry.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows=['// Generated by forest_pantry.py','namespace Delve { public static class ForestPantryCatalog {',
          'public static int Rank(string name) { switch(name.ToLowerInvariant()) {']
    for r in manifest['recipes']: rows.append(f'case "{r["name"].lower()}": return {r["rank"]};')
    rows+=['default:return 0; } }','public static string Skill(string name) { switch(name.ToLowerInvariant()) {']
    for r in manifest['recipes']: rows.append(f'case "{r["name"].lower()}": return "{r["skill"]}";')
    rows+=['default:return null; } } } }']
    (root/'src/Code/ForestPantryCatalog.generated.cs').write_text('\n'.join(rows)+'\n')
    return biomes


