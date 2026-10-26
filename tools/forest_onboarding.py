"""First-biome lessons: optional, deterministic and independent of contracts."""
from pathlib import Path
import xml.etree.ElementTree as E
from intro_story import localize

ROOT=Path(__file__).resolve().parents[1]
LESSONS={
 'Farming':('Seeds for Tomorrow','Craft a farm plot and corn seed. Find corn at Forest gardens; harvest wild plants, craft seed, plant and retain replacement seed. Farming practice comes from crops and animal harvesting.',['farmPlotBlockVariantHelper','plantedCorn1']),
 'Cooking':('Clean Water and a Hot Meal','Make a Field Hearth and Rain Collector. Put clay jars into the collector outdoors; boil the collected water with charcoal at the hearth. Cook potatoes there without needing a cooking pot.',['delveFieldHearth','delveRainCollector','drinkJarBoiledWater','foodBakedPotato']),
 'Mining':('Stone and Ore','Craft a stone shovel, then cobblestones from stone and clay. Mine marked Forest iron, coal and nitrate deposits. Mining proficiency 10 opens a Sorting Table; 20 unlocks its branch choices.',['meleeToolShovelT0StoneShovel','resourceCobblestones']),
 'Smithing':('Rekindle the Forge','Build your own Forest Forge. Process Forest iron using charcoal. Smithing practice unlocks equipment; proficiency 20 opens Forged weapons, heavy armor and tools. Recipes list the exact station and ingredients.',['delveForgeAnvil','resourceForgedIron']),
 'Carpentry':('Cloth, Shelter and Repairs','Weave cloth from grass fiber, then make a wooden storage crate. Carpentry supplies bows, casting focuses, light/medium armor and components; use trees and repair your equipment.',['resourceCloth','cntWoodWritableCrate']),
 'Alchemy':('Medicine and Runes','Make a Greenleaf Poultice and an Ember Ward Draught. Train Alchemy with useful medicine and reagents; proficiency 10 opens an Apothecary Bench and 20 opens etched runes and Arbor protection. This ward draught is NOT Arbor smoke protection.',['delveHealingPoultice','delveWardDraught']),
}

def extend(items,recipes,quests,node,prop,loc):
    qa=quests.find("append[@xpath='/quests']")
    ra=recipes.find("append[@xpath='/recipes']")
    def quest(qid,title,description,objectives,nextq=None):
        q=node(qa,'quest',id=qid)
        for k,v in {'name_key':loc(qid,title),'description_key':loc(qid+'Desc',description),'subtitle_key':qid,'offer_key':qid+'Desc','category_key':'delveQuestCategory','repeatable':'false','shareable':'false','add_to_tier_complete':'false','completiontype':'AutoComplete','icon':'ui_game_symbol_hammer'}.items():prop(q,k,v)
        for phase,name in enumerate(objectives,1):
            o=node(q,'objective',type='Craft',id=name,value=1,phase=phase);prop(o,'item',name);prop(o,'count',1)
        node(q,'reward',type='Exp',value=150)
        if nextq:node(q,'reward',type='Quest',id=nextq)
        return q
    for skill,(title,desc,objectives) in LESSONS.items():
        qid='delveLesson'+skill
        quest(qid,title,desc+' Read before crafting; objectives advance in order. These optional lessons do not count toward Wayrest contracts. Recipe knowledge is already available: proficiency, ingredients and the listed station determine access.',objectives)
        book=node(items,'item',name=qid+'Notes')
        for k,v in {'Extends':'questMaster','CustomIcon':'bookEnforcerDamage','CreativeMode':'Player','DescriptionKey':qid+'Desc','EconomicValue':500,'SellableToTrader':'false','UnlockedBy':''}.items():prop(book,k,v)
        action=node(book,'property',**{'class':'Action0'});prop(action,'Class','Quest');prop(action,'QuestGiven',qid)
        loc(qid+'Notes','Crafting Tome: '+skill)
    quest('delveSupplyLesson','Supplies for the First Incursion','Make clean water and cooked food, then a repair supply for a focus or wooden weapon. Use Crafting Tomes for step-by-step help. Prepare ammunition or runes for your chosen weapon, carry medicine, and equip any armor class. Settlement gates close on horde night: build and defend your own refuge.',['drinkJarBoiledWater','foodBakedPotato','delveFocusRepair'],'delveEmbers')
    hearth=qa.find("quest[@id='delveHearth']/reward[@type='Quest']")
    hearth.set('id','delveSupplyLesson')
    quest('delveArborPreparation','Before the Ash Road','Optional after Forest preparation: train Alchemy to proficiency 20, build the proficiency-10 Apothecary Bench, and craft Arbor Protection Draught from boiled water, Ember Salts and yarrow, all available in the Forest. Drink before entering Burnt Arbor and watch its ten-minute timer. Carry a spare or retreat before expiry. Fire and enemies still hurt. This lesson does not gate the ten-contract campaign or require defeating the Warden.',['delveArborProtection'])
    node(qa.find("quest[@id='delveEmbers']"),'reward',type='Quest',id='delveArborPreparation')
    # Native helper recipes produce a variant item; match the actual recipe output.
    for objective in qa.findall("quest[@id='delveHearth']/objective[@id='bedroll']"):
        objective.set('id','bedrollBlockVariantHelper');objective.find("property[@name='item']").set('value','bedrollBlockVariantHelper')

def apply():
    from crafting_tomes import apply as apply_tomes
    apply_tomes(ROOT/'src')
    localize('Delve',{'delveLesson'+skill+'Notes':'Crafting Tome: '+skill for skill in LESSONS})
    localize('Delve',{
      'delveArrivalDesc':'Welcome to the Living Border. Gather wood, stone and grass, then craft ANY starter weapon: dagger, cudgel, spear, handwraps, bow, wand, staff or totem, plus a Greenleaf Poultice. No fixed class is chosen. Craft one Heritage Seal if desired. Visit the Wayrest Steward, take Reclaim Wayrest and accept contracts. Character levels award talents and separate attribute points; useful actions raise proficiency. Each skill has two fundamentals at proficiency 10 and three branch entries at 20; each purchase costs one talent and branch entries require both fundamentals.',
      'delveFieldGuideDesc':'READ to begin the Forest preparation chain. Gather, choose any starter weapon, establish a refuge, then secure water, food and repairs. Buy optional Crafting Tomes for 500 gold each from vendors, or ask the Wayrest Steward about training. Every restock includes at least three different tome types. All early recipe knowledge is available without random books: train the owning proficiency, gather ingredients and use the listed station. Character level and proficiency are separate. Take Reclaim Wayrest from the Steward: ten returned contracts advance the settlement. Defeating the Ashbound Warden advances the independent champion campaign. The Warden arrives two game-hours before dawn. NPC settlements close during incursions. Prepare your own defenses. Optional Arbor preparation follows the Forest lessons.',
    })

    path=ROOT/'src/DelveWayrest/Config/dialogs.xml'
    tree=E.parse(path);dialog=tree.find('.//dialog');start=dialog.find("statement[@id='start']")
    if dialog.find("response[@id='delveTraining']") is None:
        E.SubElement(start,'response_entry',id='delveTraining')
        E.SubElement(dialog,'response',id='delveTraining',text='delveTrainingAsk',nextstatementid='delveTraining')
        s=E.SubElement(dialog,'statement',id='delveTraining',text='delveTrainingReply');E.SubElement(s,'response_entry',id='nevermind')
    E.indent(tree);tree.write(path,encoding='utf-8',xml_declaration=True)
    localize('DelveWayrest',{
      'delveTrainingAsk':'Where can I learn our crafts?',
      'delveTrainingReply':'Vendors sell Crafting Tomes for Farming, Cooking, Mining, Smithing, Carpentry and Alchemy for 500 gold each. Every inventory restock includes at least three different tome types. Buy a tome and READ it to track an optional lesson about recipes and stations. Tomes are not craftable and are not required to unlock recipes or stations. Craft before reading a tome and you may need to make the lesson items again: read first. These lessons are separate from the ten contracts. Each skill opens two fundamentals at proficiency 10 and three branch choices at 20; character levels supply the points to buy them.',
      'delveWayrestRefuge':'Read your Field Guide and follow its preparation journal. Choose any starter weapon, establish a Settlement Stone, bedroll and campfire outside Wayrest, then secure food, clean water, healing, ammunition and repairs. Ask about our crafts for optional Crafting Tomes. Take woodland contracts and return them for payment. Both quests can progress independently: you need not defeat the Warden to complete our ten contracts.',
      'delveWayrestOnwardDesc':'Wayrest has ten completed contracts. Before following the road to Arbor Camp, train Alchemy to proficiency 20 and craft Arbor Protection Draught at an Apothecary Bench: one boiled water, three Ember Salts, two yarrow. All inputs are available in the Forest. Drink before crossing; carry a spare or retreat before its ten-minute timer expires. The Field Guide preparation chain teaches this route. Arrival at Arbor Camp advances the settlement campaign independently of Warden victory.',
    })

if __name__=='__main__':
    apply()

