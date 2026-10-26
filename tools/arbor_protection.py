"""Forest-crafted protection bound to the installed Burnt Forest hazard system."""
from copy import deepcopy

def extend(vanilla,items,recipes,buffs,node,prop,loc):
    item=deepcopy(vanilla['items'].find(".//item[@name='drinkJarBoiledWater']"))
    item.set('name','delveArborProtection')
    for child in list(item):
        if child.tag=='effect_group':item.remove(child)
    for key,value in {'CustomIcon':'drinkJarRedTea','DescriptionKey':'delveArborProtectionDesc','UnlockedBy':'','Stacknumber':10,'EconomicValue':0,'SellableToTrader':'false','Tags':'drink,delveArborProtection,delveProcessing'}.items():
        old=item.find("property[@name='%s']"%key)
        if old is not None:old.set('value',str(value))
        else:prop(item,key,value)
    eg=node(item,'effect_group',tiered='false')
    node(eg,'triggered_effect',trigger='onSelfPrimaryActionEnd',action='AddBuff',buff='delveArborProtected')
    items.append(item)
    loc('delveArborProtection','Arbor Protection Draught')
    loc('delveArborProtectionDesc','Alchemy proficiency 20. At an Apothecary Bench combine 1 boiled water, 3 Ember Salts and 2 Yarrow. Drink before entering Burnt Arbor: 10 real-time minutes of protection from its native smoke hazard and smoke-storm health/stamina damage. Does not protect against enemies, fire attacks or other biomes. Re-drinking refreshes; it does not stack. Death removes protection. All ingredients are renewable in the Forest.')
    b=node(buffs,'buff',name='delveArborProtected',name_key='delveArborProtected',description_key='delveArborProtectedDesc',icon='ui_game_symbol_burnt_hazard',remove_on_death='true')
    node(b,'stack_type',value='replace');node(b,'duration',value=600)
    eg=node(b,'effect_group')
    node(eg,'triggered_effect',trigger='onSelfBuffStart',action='RemoveBuff',buff='buffBurnt_Hazard01,buffBurnt_Hazard02')
    loc('delveArborProtected','Arbor Protection')
    loc('delveArborProtectedDesc','Burnt Arbor smoke hazard and smoke-storm damage are suppressed while this timer remains. Ordinary combat and fire still hurt. Leave Arbor or drink another draught before it expires.')
    # Append conditions to native effects, not a second damage/timer simulation.
    # Keeping the main hazard and storm state machines alive preserves expiry,
    # shelter recovery and native biome achievements.

def patch(root,node):
    paths=[
      "/buffs/buff[@name='buffBurnt_Hazard']/effect_group/triggered_effect[@buff='buffBurnt_Hazard01' or @buff='buffBurnt_Hazard02']",
      "/buffs/buff[@name='buffBurnt_Hazard']/effect_group[@name='Update Time']",
      "/buffs/buff[@name='buffBurnt_Storm_Stage01' or @name='buffBurnt_Storm_Stage02' or @name='buffBurnt_Storm_Recover01']/effect_group[passive_effect[@name='StaminaMaxBlockage'] or triggered_effect[@action='AddHealth']]",
    ]
    for path in paths:
        append=node(root,'append',xpath=path)
        node(append,'requirement',name='!HasBuff',buff='delveArborProtected')

