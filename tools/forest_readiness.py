"""Close first-horde supply gaps. No debug grants or later-biome ingredients."""
from xml.etree import ElementTree as E
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
# Only these native recipes are advertised as part of the Forest slice.
NATIVE={
 'ammoArrowStone':('Carpentry',1),'ammoCrossbowBoltStone':('Carpentry',1),
 'campfire':('Carpentry',1),'keystoneBlock':('Carpentry',1),
 'frameShapes:VariantHelper':('Carpentry',1),'woodLogPillar100':('Carpentry',1),
 'bedrollBlockVariantHelper':('Carpentry',1),'cntWoodWritableCrate':('Carpentry',1),
 'oldWoodDoor':('Carpentry',1),'woodHatch':('Carpentry',1),'ladderWood':('Carpentry',1),
 'trapSpikesWoodDmg0':('Carpentry',1),'cobblestoneShapes:VariantHelper':('Mining',10),
 'resourceCobblestones':('Mining',1),'resourceDuctTape':('Carpentry',1),
 'meleeToolRepairT0StoneAxe':('Carpentry',1),'meleeToolShovelT0StoneShovel':('Carpentry',1),
 'meleeToolTorch':('Carpentry',1),'medicalSplint':('Alchemy',1),
 'medicalBandage':('Alchemy',1),'foodCornMeal':('Cooking',1),
 'farmPlotBlockVariantHelper':('Farming',1),
}
NATIVE.update({'armorPrimitive'+slot:('Carpentry',1) for slot in ('Helmet','Outfit','Gloves','Boots')})
STARTER_WEAPONS={
 'meleeWpnClubT0WoodenClub':{'resourceWood':5},
 'gunBowT0PrimitiveBow':{'resourceWood':8,'resourceYuccaFibers':3},
 'meleeWpnBladeT0BoneKnife':{'resourceBone':5},
}
NATIVE.update({name:('Carpentry',1) for name in STARTER_WEAPONS})
FOREST_SEEDS=['Corn','Potato','Pumpkin','Mushroom','Blueberry','Cotton','Chrysanthemum','Goldenrod']
NATIVE.update({'planted'+s+'1':('Farming',1) for s in FOREST_SEEDS})

def extend(base,blocks,items,recipes,entities,node,prop,loc):
    ra=recipes.find("append[@xpath='/recipes']")
    manifest=[]
    def recipe(name,ingredients,skill,rank=1,count=1,station=None):
        r=node(ra,'recipe',name=name,count=count,craft_time=15)
        if station:r.set('craft_area',station)
        for k,v in ingredients.items():node(r,'ingredient',name=k,count=v)
        manifest.append(dict(name=name,ingredients=ingredients,skill=skill,rank=rank,count=count,station=station or ''))
    # Primitive armor is known immediately, with no native book/quality gates.
    for slot in ('Helmet','Outfit','Gloves','Boots'):
        name='armorPrimitive'+slot
        node(recipes,'remove',xpath="/recipes/recipe[@name='%s']"%name)
        replacement=node(recipes,'append',xpath='/recipes')
        r=node(replacement,'recipe',name=name,count=1,craft_time=5)
        node(r,'ingredient',name='resourceYuccaFibers',count=5)
        node(r,'ingredient',name='resourceWood',count=5)
    # Starter weapons are known inventory recipes, retaining native material costs.
    for name,ingredients in STARTER_WEAPONS.items():
        node(recipes,'remove',xpath="/recipes/recipe[@name='%s']"%name)
        replacement=node(recipes,'append',xpath='/recipes')
        r=node(replacement,'recipe',name=name,count=1,craft_time=5)
        for ingredient,count in ingredients.items():node(r,'ingredient',name=ingredient,count=count)
    # Alternate fletching and lighting remove dependence on nest/fat drop luck.
    for ammo in ('ammoArrowStone','ammoCrossbowBoltStone'):
        recipe(ammo,{'resourceRockSmall':2,'resourceWood':2,'resourceYuccaFibers':2},'Carpentry',count=2)
    recipe('meleeToolTorch',{'resourceWood':2,'resourceCloth':2,'delveCharcoal':1},'Carpentry')
    recipe('resourceCrushedSand',{'resourceRockSmall':2},'Mining',station='delveSortingTable',count=4)
    recipe('medicalPlasterCast',{'resourceCloth':8,'foodCornMeal':2,'resourceCrushedSand':2,'drinkJarBoiledWater':1},'Alchemy',20,station='delveFieldHearth')
    recipe('foodBakedPotato',{'foodCropPotato':2,'delveCharcoal':1},'Cooking',station='delveFieldHearth')
    recipe('foodGrilledMeat',{'foodRawMeat':3,'delveCharcoal':1},'Cooking',station='delveFieldHearth')
    # Forest stumps already host the native bee encounter; make the honey payout
    # dependable without introducing a fictitious honey-manufacturing recipe.
    a=node(blocks,'append',xpath="/blocks/block[@name='treeStump']")
    node(a,'drop',event='Destroy',name='foodHoney',count=1,prob=1)
    it=node(items,'item',name='delveForestReadinessGuide')
    for k,v in {'Extends':'resourcePaper','CustomIcon':'resourcePaper','DescriptionKey':'delveForestReadinessGuideDesc','CreativeMode':'Player','UnlockedBy':'','EconomicValue':0,'SellableToTrader':'false'}.items():prop(it,k,v)
    loc('delveForestReadinessGuide','Forest: First Horde Crafting Guide')
    loc('delveForestReadinessGuideDesc','Forest recipes use crafting proficiency 1-20, independent of character level. Gather wood, stone, grass, clay and marked iron/nitrate. Craft a stone axe, shovel, bedroll, frames, storage, doors and spikes. Build a Field Hearth, Forest Forge and Rain Collector; make charcoal, jars, water, cloth and repairs. Native Forest stumps guarantee honey. Gardens supply crop seeds; wildlife supplies meat, hides and bone. At proficiency 10 make processing benches; at 20 forge upgraded weapons, armor and tools and inscribe etched runes. Alternate stone arrows/bolts use fiber instead of feathers. Later-biome/native recipes outside this catalogue are unavailable in this playtest. Read START-HERE.txt for full routes and horde preparation.')
    recipe('delveForestReadinessGuide',{'resourceYuccaFibers':1},None)
    for op in entities.findall('set'):
        if 'ItemsOnEnterGame' in op.get('xpath',''):op.text+=',delveForestReadinessGuide'
    (ROOT/'src/Forest/readiness.json').write_text(json.dumps({'recipes':manifest,'native':NATIVE},indent=2)+'\n')
